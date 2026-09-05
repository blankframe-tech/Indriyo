"""
Unit tests for Indriyo Web Server and MJPEG / Telemetry Streaming.
"""

import time
import json
import urllib.request
import numpy as np

from indriyo_core.web_server import ADASStreamServer
from indriyo_core.ttc_calculator import ADASThreatSummary, ThreatLevel
from indriyo_core.telemetry import TelemetryData


def test_web_server_initialization_and_endpoints():
    server = ADASStreamServer(host="127.0.0.1", port=8991)
    server.start()

    time.sleep(0.3)

    try:
        # 1. Test /telemetry when empty
        req = urllib.request.Request("http://127.0.0.1:8991/telemetry")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert isinstance(data, dict)

        # 2. Update frame, threat, and telemetry
        summary = ADASThreatSummary(
            highest_threat=ThreatLevel.WARNING,
            left_blind_spot_active=True,
            right_blind_spot_active=False,
            critical_collision_warning=False,
            minimum_ttc_seconds=1.45,
            threat_count=1,
            threat_reports=[]
        )
        telemetry = TelemetryData(speed_kmh=65.0, rpm=5500)
        dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)

        server.update_frame(dummy_frame, threat_summary=summary, telemetry=telemetry)

        # 3. Test updated /telemetry
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["highest_threat"] == "WARNING"
            assert data["left_blind_spot"] is True
            assert data["min_ttc"] == 1.45
            assert data["speed_kmh"] == 65.0

        # 4. Test root mirror UI
        root_req = urllib.request.Request("http://127.0.0.1:8991/mirror")
        with urllib.request.urlopen(root_req, timeout=2.0) as resp:
            assert resp.status == 200
            html = resp.read().decode()
            assert "Indriyo Cockpit HUD Mirror" in html
            assert "/stream" in html

    finally:
        server.stop()
