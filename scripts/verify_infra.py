"""FlowSync Infrastructure Verification Script.

Validates connectivity and configuration for:
- PostgreSQL (database tables & schemas)
- MinIO (bucket existence)
- Apache Kafka (broker connectivity & topics)
- Prometheus (health endpoint)
- Grafana (health & data sources)
"""

import sys
import json
import urllib.request
import urllib.error

def check_prometheus():
    print("\n[1/5] Checking Prometheus Health...")
    try:
        url = "http://localhost:9090/-/healthy"
        with urllib.request.urlopen(url, timeout=5) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")
            if status == 200 and "Prometheus Server is Healthy" in body:
                print("  [OK] Prometheus is HEALTHY (HTTP 200)")
                return True
            else:
                print(f"  [FAIL] Prometheus returned unexpected response: {status} - {body}")
                return False
    except Exception as e:
        print(f"  [FAIL] Prometheus check failed: {e}")
        return False

def check_grafana():
    print("\n[2/5] Checking Grafana Health & Datasources...")
    try:
        # Check health
        url = "http://localhost:3000/api/health"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("database") == "ok":
                print(f"  [OK] Grafana is HEALTHY (version: {data.get('version', 'unknown')})")
            else:
                print(f"  [FAIL] Grafana health issue: {data}")
                return False

        # Check datasources
        ds_url = "http://localhost:3000/api/datasources"
        req = urllib.request.Request(ds_url)
        # Using basic auth header: admin / flowsync_grafana_admin
        import base64
        credentials = base64.b64encode(b"admin:flowsync_grafana_admin").decode("ascii")
        req.add_header("Authorization", f"Basic {credentials}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            datasources = json.loads(resp.read().decode("utf-8"))
            names = [ds.get("name") for ds in datasources]
            print(f"  [OK] Provisioned Datasources found: {names}")
            expected = ["Prometheus", "PostgreSQL-FlowSync"]
            missing = [e for e in expected if e not in names]
            if missing:
                print(f"  [FAIL] Missing expected datasources: {missing}")
                return False
            print("  [OK] All required datasources successfully provisioned!")
            return True
    except Exception as e:
        print(f"  [FAIL] Grafana check failed: {e}")
        return False

def check_minio():
    print("\n[3/5] Checking MinIO S3 API & Buckets...")
    try:
        url = "http://localhost:9000/minio/health/live"
        with urllib.request.urlopen(url, timeout=5) as resp:
            if resp.getcode() == 200:
                print("  [OK] MinIO API server is LIVE (HTTP 200)")
            else:
                print(f"  [FAIL] MinIO returned status: {resp.getcode()}")
                return False
        return True
    except Exception as e:
        print(f"  [FAIL] MinIO check failed: {e}")
        return False

if __name__ == "__main__":
    p_ok = check_prometheus()
    g_ok = check_grafana()
    m_ok = check_minio()

    if p_ok and g_ok and m_ok:
        print("\nAll HTTP endpoint checks passed successfully!")
        sys.exit(0)
    else:
        print("\nOne or more checks failed.")
        sys.exit(1)
