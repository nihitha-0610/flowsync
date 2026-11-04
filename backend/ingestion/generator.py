"""FlowSync - Multi-Device Synthetic Event Generator.

Generates realistic industrial IoT telemetry streams with configurable rates,
multi-device baseline physics, subtle anomaly patterns, and chaos corruption.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from core.config import get_settings
from core.event_contract import (
    CanonicalTelemetryEvent,
    PHYSICAL_RANGES,
    StatusCode,
)
from ingestion.corruption import CorruptionInjector, CorruptionKind
from ingestion.producer import KafkaEventProducer

logger = logging.getLogger("flowsync.ingestion.generator")


class AnomalyPattern(str, Enum):
    """Categorized synthetic anomaly patterns for ML testing."""
    SPIKE = "anomaly:spike"
    DRIFT = "anomaly:drift"
    CORRELATED_FAULT = "anomaly:correlated_fault"


class GeneratorConfig(BaseModel):
    """Configuration parameters for the synthetic telemetry generator."""
    num_devices: int = Field(default=10, ge=1, le=500)
    events_per_second: float = Field(default=10.0, ge=0.1, le=5000.0)
    corruption_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    anomaly_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    seed: Optional[int] = Field(default=None)
    facilities: List[str] = Field(default=["FAC-01", "FAC-02", "FAC-03"])
    target_topic: Optional[str] = Field(default=None)


class DeviceBaseline:
    """Individual device baseline state, operational profile, and drift tracking."""

    def __init__(self, device_id: str, facility_id: str, rng: random.Random):
        self.device_id = device_id
        self.facility_id = facility_id
        self.location = f"Zone-{rng.choice(['A', 'B', 'C', 'D'])}-{rng.randint(1, 4)}"

        # Nominal operating baselines
        self.base_temp = rng.uniform(40.0, 75.0)
        self.base_vibration = rng.uniform(1.0, 4.0)
        self.base_pressure = rng.uniform(30.0, 60.0)
        self.base_flow = rng.uniform(100.0, 250.0)
        self.base_power = rng.uniform(15.0, 45.0)

        # Dynamic drift offsets
        self.drift_temp = 0.0
        self.drift_vibration = 0.0
        self.drift_pressure = 0.0


class SyntheticEventGenerator:
    """High-throughput industrial telemetry stream generator."""

    def __init__(
        self,
        config: Optional[GeneratorConfig] = None,
        producer: Optional[KafkaEventProducer] = None,
    ):
        self.config = config or GeneratorConfig()
        self.settings = get_settings()
        self.target_topic = self.config.target_topic or self.settings.KAFKA_TOPIC_RAW

        self._producer = producer
        self._rng = random.Random(self.config.seed)
        self._corruption_injector = CorruptionInjector(seed=self.config.seed)

        # Initialize virtual device fleet
        self._devices: List[DeviceBaseline] = []
        self._init_devices()

        # Threading and lifecycle control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._generated_count = 0
        self._anomalies_count = 0
        self._corruptions_count = 0
        self._lock = threading.Lock()

    def _init_devices(self):
        """Construct the simulated fleet of devices."""
        self._devices.clear()
        for i in range(1, self.config.num_devices + 1):
            dev_id = f"DEV-{i:04d}"
            fac_id = self._rng.choice(self.config.facilities)
            self._devices.append(DeviceBaseline(dev_id, fac_id, self._rng))

    def update_config(self, new_config: GeneratorConfig):
        """Safely update generator configuration parameters dynamically."""
        with self._lock:
            self.config = new_config
            if new_config.seed is not None:
                self._rng.seed(new_config.seed)
                self._corruption_injector = CorruptionInjector(seed=new_config.seed)
            self._init_devices()
            logger.info("Updated generator configuration: %s", new_config)

    def generate_single_event(
        self,
        device: Optional[DeviceBaseline] = None,
        timestamp_override: Optional[datetime] = None,
    ) -> Tuple[Dict[str, Any] | str, str]:
        """Generate a single telemetry event with optional anomaly or corruption.
        
        Returns:
            Tuple of (payload, header_label)
        """
        if device is None:
            device = self._rng.choice(self._devices)

        now = timestamp_override or datetime.now(timezone.utc)
        ts_str = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Determine label and pattern
        roll = self._rng.random()
        is_corruption = roll < self.config.corruption_rate
        is_anomaly = not is_corruption and roll < (self.config.corruption_rate + self.config.anomaly_rate)

        # 1. Base normal signal generation with minor Gaussian noise
        temp = device.base_temp + self._rng.gauss(0, 1.2) + device.drift_temp
        vibe = max(0.01, device.base_vibration + self._rng.gauss(0, 0.2) + device.drift_vibration)
        press = device.base_pressure + self._rng.gauss(0, 1.5) + device.drift_pressure
        flow = max(0.0, device.base_flow + self._rng.gauss(0, 3.0))
        power = max(0.0, device.base_power + self._rng.gauss(0, 0.8))
        status = StatusCode.OK

        label = "normal"

        # 2. Inject subtle anomaly patterns (strictly staying within valid physical bounds!)
        if is_anomaly:
            pattern = self._rng.choice(list(AnomalyPattern))
            label = pattern.value

            if pattern == AnomalyPattern.SPIKE:
                # Sudden transient jump within physical limits
                temp = min(PHYSICAL_RANGES["temperature"][1] - 5.0, temp + self._rng.uniform(25.0, 40.0))
                vibe = min(PHYSICAL_RANGES["vibration"][1] - 1.0, vibe + self._rng.uniform(4.0, 7.0))
                status = StatusCode.WARNING

            elif pattern == AnomalyPattern.DRIFT:
                # Cumulative mechanical wear simulation
                device.drift_temp += self._rng.uniform(0.1, 0.3)
                device.drift_vibration += self._rng.uniform(0.02, 0.05)
                temp = min(PHYSICAL_RANGES["temperature"][1] - 2.0, temp + device.drift_temp)
                vibe = min(PHYSICAL_RANGES["vibration"][1] - 0.5, vibe + device.drift_vibration)
                status = StatusCode.WARNING if device.drift_temp > 15.0 else StatusCode.OK

            elif pattern == AnomalyPattern.CORRELATED_FAULT:
                # Inverse relationship anomaly: pressure drop causing flow increase and power surge
                press = max(PHYSICAL_RANGES["pressure"][0] + 1.0, press - 20.0)
                flow = min(PHYSICAL_RANGES["flow_rate"][1] - 10.0, flow + 150.0)
                power = min(PHYSICAL_RANGES["power_consumption"][1] - 5.0, power + 35.0)
                status = StatusCode.CRITICAL

        # Bound check to guarantee schema compliance before corruption
        temp = max(PHYSICAL_RANGES["temperature"][0], min(PHYSICAL_RANGES["temperature"][1], temp))
        vibe = max(PHYSICAL_RANGES["vibration"][0], min(PHYSICAL_RANGES["vibration"][1], vibe))
        press = max(PHYSICAL_RANGES["pressure"][0], min(PHYSICAL_RANGES["pressure"][1], press))
        flow = max(PHYSICAL_RANGES["flow_rate"][0], min(PHYSICAL_RANGES["flow_rate"][1], flow))
        power = max(PHYSICAL_RANGES["power_consumption"][0], min(PHYSICAL_RANGES["power_consumption"][1], power))

        event_dict: Dict[str, Any] = {
            "event_id": str(uuid4()),
            "device_id": device.device_id,
            "facility_id": device.facility_id,
            "timestamp": ts_str,
            "temperature": round(temp, 2),
            "vibration": round(vibe, 3),
            "pressure": round(press, 2),
            "flow_rate": round(flow, 2),
            "power_consumption": round(power, 2),
            "status_code": status.value,
            "location": device.location,
        }

        # 3. Inject chaos/corruption if chosen
        if is_corruption:
            corrupted_payload, kind, reason = self._corruption_injector.inject(event_dict)
            label = f"corruption:{kind.value}"
            with self._lock:
                self._corruptions_count += 1
            return corrupted_payload, label

        with self._lock:
            self._generated_count += 1
            if is_anomaly:
                self._anomalies_count += 1

        return event_dict, label

    def generate_batch(self, count: int) -> List[Tuple[Dict[str, Any] | str, str]]:
        """Synchronously generate a deterministic batch of events."""
        return [self.generate_single_event() for _ in range(count)]

    def _run_loop(self):
        """Internal generator loop running in dedicated thread."""
        logger.info(
            "Synthetic event generator started (Rate: %.1f eps, Devices: %d)",
            self.config.events_per_second,
            self.config.num_devices,
        )
        tick_interval = 0.1  # 100ms bursts
        events_per_tick = max(1, int(self.config.events_per_second * tick_interval))

        while self._running:
            tick_start = time.perf_counter()

            for _ in range(events_per_tick):
                if not self._running:
                    break
                payload, label = self.generate_single_event()

                if self._producer:
                    headers = {
                        "x-source": "synthetic",
                        "x-synthetic-label": label,
                    }
                    key = payload.get("device_id") if isinstance(payload, dict) else None
                    self._producer.publish(
                        topic=self.target_topic,
                        value=payload,
                        key=key,
                        headers=headers,
                    )

            elapsed = time.perf_counter() - tick_start
            sleep_time = max(0.0, tick_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self):
        """Start the background generation thread."""
        with self._lock:
            if self._running:
                logger.warning("Generator is already running.")
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="FlowSyncGeneratorThread")
            self._thread.start()

    def stop(self):
        """Stop the background generation thread and flush producer."""
        with self._lock:
            if not self._running:
                return
            self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        if self._producer:
            self._producer.flush(timeout=5.0)
        logger.info("Synthetic event generator stopped.")

    def status(self) -> Dict[str, Any]:
        """Return operational state and telemetry production metrics."""
        with self._lock:
            return {
                "running": self._running,
                "config": self.config.model_dump(),
                "generated_count": self._generated_count,
                "anomalies_count": self._anomalies_count,
                "corruptions_count": self._corruptions_count,
            }

