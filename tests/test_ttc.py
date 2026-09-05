"""
Unit tests for Indriyo Time-To-Collision (TTC) and Blind Spot Threat Engine.
"""

import pytest
from indriyo_core.ttc_calculator import TTCCalculator, ThreatLevel, ThreatZone
from indriyo_core.tracker import TrackedVehicle
from indriyo_core.detector import Detection
from indriyo_core.telemetry import TelemetryData


def create_mock_track(track_id: int, box, optical_tau: float = 99.0, class_name: str = "car") -> TrackedVehicle:
    det = Detection(box=box, confidence=0.9, class_name=class_name, class_id=2)
    track = TrackedVehicle(track_id=track_id, initial_detection=det, timestamp=100.0)
    track.optical_tau = optical_tau
    return track


def test_stationary_bike_rapid_approaching_vehicle():
    """
    PRD Rule: If motorcycle is stationary at a red light (0 km/h),
    a vehicle approaching at high relative speed must trigger CRITICAL.
    """
    calc = TTCCalculator()
    # Vehicle in center rear, optical tau = 1.4s (fast approach)
    # 800x480 frame, box in center
    track = create_mock_track(track_id=1, box=(350, 200, 450, 320), optical_tau=1.4)
    telemetry = TelemetryData(speed_kmh=0.0)

    summary = calc.assess_threats([track], (480, 800), telemetry)
    assert summary.highest_threat == ThreatLevel.CRITICAL
    assert summary.critical_collision_warning is True
    assert summary.minimum_ttc_seconds <= 1.8


def test_left_blind_spot_detection():
    """
    Vehicle in left zone (x < 0.35 * width) close to motorcycle should trigger WARNING.
    """
    calc = TTCCalculator()
    # Box located on left side: x1=40, x2=160 (center=100 / 800 = 0.125)
    # Large height = close proximity (~5m)
    track = create_mock_track(track_id=2, box=(40, 250, 180, 420), optical_tau=99.0)
    telemetry = TelemetryData(speed_kmh=60.0)

    summary = calc.assess_threats([track], (480, 800), telemetry)
    assert summary.left_blind_spot_active is True
    assert summary.highest_threat == ThreatLevel.WARNING
    assert summary.threat_reports[0].threat_zone == ThreatZone.LEFT_BLIND_SPOT


def test_safe_pacing_vehicle_on_highway():
    """
    Vehicle cruising at same speed far behind (tau=99.0, large distance) is CLEAR or MONITORING.
    """
    calc = TTCCalculator()
    # Small box far away: h=30px, distance ~25m
    track = create_mock_track(track_id=3, box=(380, 220, 420, 250), optical_tau=99.0)
    telemetry = TelemetryData(speed_kmh=80.0)

    summary = calc.assess_threats([track], (480, 800), telemetry)
    assert summary.highest_threat in (ThreatLevel.CLEAR, ThreatLevel.MONITORING)
    assert summary.critical_collision_warning is False
    assert summary.left_blind_spot_active is False
    assert summary.right_blind_spot_active is False
