"""
Project ASTRA - Mock Android Telemetry Stream Simulator
Simulates Darshan's Android ForegroundService sending telemetry to the ASTRA Backend.
CHRIST (Deemed to be University), Department of CSE

Usage:
  python tests/mock_android_client.py
  python tests/mock_android_client.py --url http://127.0.0.1:8000
"""

import sys
import time
import argparse
import requests
from typing import Dict, Any

# Ensure stdout supports UTF-8 on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_scenario(
    base_url: str,
    scenario_num: int,
    title: str,
    payload: Dict[str, Any],
    expected_risk: str,
    expected_trigger: bool
) -> bool:
    endpoint = f"{base_url.rstrip('/')}/api/v1/telemetry/score"
    print("\n" + "-" * 75)
    print(f">> [STREAM EVENT #{scenario_num}] {title}")
    print("-" * 75)
    print(f"  Target Endpoint : {endpoint}")
    print(f"  Telemetry Ingest:")
    print(f"    * User ID       : {payload['user_id']}")
    print(f"    * Coordinates   : ({payload['latitude']}, {payload['longitude']})")
    print(f"    * Route Detour  : {payload['deviation_meters']} m")
    print(f"    * Dwell / Stop  : {payload['stop_duration_seconds']} s")
    print(f"    * Speed         : {payload['speed_kmh']} km/h")
    print(f"    * Time of Day   : {payload['hour_of_day']}:00 hrs")

    start_time = time.time()
    try:
        response = requests.post(endpoint, json=payload, timeout=5.0)
        latency_ms = (time.time() - start_time) * 1000.0

        if response.status_code == 200:
            res_data = response.json()
            risk_level = res_data.get("risk_level")
            risk_code = res_data.get("risk_code")
            confidence = res_data.get("confidence", 0.0)
            trigger_evidence = res_data.get("trigger_evidence_capture", False)

            trigger_status = "[ALERT ACTIVATED: Evidence Capture Triggered]" if trigger_evidence else "[STANDBY]"

            print(f"\n  << Response ({response.status_code} OK | Latency: {latency_ms:.1f}ms):")
            print(f"    * Risk Level    : {risk_level} (Risk Code: {risk_code})")
            print(f"    * Confidence    : {confidence * 100:.1f}%")
            print(f"    * Agent 4 Trigger: {trigger_evidence} {trigger_status}")

            # Validate against expectations
            passed = (risk_level == expected_risk and trigger_evidence == expected_trigger)
            status_text = "[PASSED]" if passed else f"[FAILED] (Expected: {expected_risk}, Trigger: {expected_trigger})"
            print(f"\n  Result Verification: {status_text}")
            return passed
        else:
            print(f"\n  [ERROR] Server Error: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"\n  [ERROR] Connection Error: Unable to connect to {base_url}.")
        print("          Please ensure the ASTRA backend is running:")
        print("          uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"\n  [ERROR] Unexpected error: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Project ASTRA - Mock Android Client Telemetry Streamer"
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Backend base URL (default: http://127.0.0.1:8000)"
    )
    args = parser.parse_args()

    print("=" * 75)
    print("Project ASTRA: Android Telemetry Simulator (Agent 1 & Agent 4 Pipeline)")
    print("Client Lead  : Darshan R (Android)")
    print("Backend Lead : Kasine RS (ML & Microservice)")
    print("Institution  : CHRIST (Deemed to be University), Department of CSE")
    print("=" * 75)

    # 1. Health check probe
    try:
        health_resp = requests.get(f"{args.url.rstrip('/')}/health", timeout=3.0)
        if health_resp.status_code == 200:
            print(f"[OK] Backend Health Check: ONLINE ({health_resp.json()})")
        else:
            print(f"[WARNING] Health check returned status: {health_resp.status_code}")
    except Exception as e:
        print(f"[ERROR] Backend is offline at {args.url}. Please start the server first.")
        print("        Command: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

    scenarios = [
        {
            "num": 1,
            "title": "Daytime Regular Commute (Safe Transit)",
            "payload": {
                "user_id": "darshan_device_01",
                "latitude": 12.934533,
                "longitude": 77.606041,
                "deviation_meters": 10.0,
                "stop_duration_seconds": 0.0,
                "speed_kmh": 45.0,
                "hour_of_day": 14
            },
            "expected_risk": "Safe",
            "expected_trigger": False
        },
        {
            "num": 2,
            "title": "Evening Commute Traffic Signal Pause (Safe Transit)",
            "payload": {
                "user_id": "darshan_device_01",
                "latitude": 12.935000,
                "longitude": 77.607000,
                "deviation_meters": 20.0,
                "stop_duration_seconds": 90.0,
                "speed_kmh": 0.0,
                "hour_of_day": 18
            },
            "expected_risk": "Safe",
            "expected_trigger": False
        },
        {
            "num": 3,
            "title": "Critical Midnight Off-Route Halt (Anomaly -> Agent 4 Trigger)",
            "payload": {
                "user_id": "darshan_device_01",
                "latitude": 12.910000,
                "longitude": 77.590000,
                "deviation_meters": 550.0,
                "stop_duration_seconds": 400.0,
                "speed_kmh": 0.0,
                "hour_of_day": 23
            },
            "expected_risk": "Critical",
            "expected_trigger": True
        }
    ]

    all_passed = True
    for sc in scenarios:
        passed = run_scenario(
            base_url=args.url,
            scenario_num=sc["num"],
            title=sc["title"],
            payload=sc["payload"],
            expected_risk=sc["expected_risk"],
            expected_trigger=sc["expected_trigger"]
        )
        if not passed:
            all_passed = False
        time.sleep(0.3)

    print("\n" + "=" * 75)
    if all_passed:
        print("[SUCCESS] ALL SIMULATION SCENARIOS PASSED SUCCESSFULLY!")
        print("          Agent 1 Risk Engine & Agent 4 Trigger Pipeline ready for Android integration.")
    else:
        print("[WARNING] Some scenarios did not match expected outcomes.")
    print("=" * 75)


if __name__ == "__main__":
    main()
