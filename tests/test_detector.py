"""
Unit tests for Detector and HUD Renderer.
"""

import numpy as np
from indriyo_core.detector import VisionHeuristicDetector
from indriyo_core.hud_renderer import HUDRenderer
from indriyo_core.synthetic_stream import SyntheticRearviewStream
from indriyo_core.ttc_calculator import TTCCalculator
from indriyo_core.telemetry import TelemetryData


def test_detector_runs_on_synthetic_frame():
    stream = SyntheticRearviewStream(width=640, height=360, scenario="tailgater")
    ret, frame = stream.get_frame()
    assert ret is True
    assert frame is not None

    detector = VisionHeuristicDetector()
    detections = detector.detect(frame)
    # The synthetic frame has a vehicle with clear contrast
    assert isinstance(detections, list)


def test_hud_renderer_output_integrity():
    renderer = HUDRenderer(target_width=800, target_height=480)
    blank_frame = np.zeros((480, 800, 3), dtype=np.uint8)

    ttc_calc = TTCCalculator()
    summary = ttc_calc.assess_threats([], (480, 800), TelemetryData(speed_kmh=50.0))

    hud = renderer.render(
        frame=blank_frame,
        threat_summary=summary,
        telemetry=TelemetryData(speed_kmh=50.0),
        fps=30.0,
        latency_ms=12.0
    )

    assert hud.shape == (480, 800, 3)
    assert hud.dtype == np.uint8
