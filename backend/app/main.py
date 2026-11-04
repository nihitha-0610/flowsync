"""FlowSync - Real-Time Streaming Analytics & Data Quality Backend API.

FastAPI application providing health probes, operational metrics, telemetry access,
Great Expectations validation reports, and AI anomaly detection endpoints.
"""

from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import anomalies, events, health, ingest, metrics, quality

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("flowsync.api")

app = FastAPI(
    title="FlowSync Telemetry & AI Anomaly Detection API",
    description="Real-Time Industrial IoT Data Engineering Pipeline API with Great Expectations and Isolation Forest Anomaly Detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(health.router)
app.include_router(events.router)
app.include_router(metrics.router)
app.include_router(quality.router)
app.include_router(anomalies.router)
app.include_router(ingest.router)


@app.get("/", tags=["Root"])
def root():
    """Root entrypoint returning pipeline API metadata."""
    return {
        "service": "FlowSync Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
    }

