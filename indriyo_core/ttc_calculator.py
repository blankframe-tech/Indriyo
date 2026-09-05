"""
Indriyo - Time-To-Collision (TTC) and Blind Spot Threat Assessment Engine
Implements Optical Tau expansion theory, geometric distance triangulation,
and speed-adaptive threat filtering via OBD-II/GPS telemetry.
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import math
from indriyo_core.tracker import TrackedVehicle
from indriyo_core.telemetry import TelemetryData


class ThreatLevel(IntEnum):
    CLEAR = 0       # All clear, no immediate threats (Green / Passive)
    MONITORING = 1  # Vehicles detected in vicinity, safe distance (Cyan / Subtle)
    WARNING = 2     # Amber alert: Vehicle in Blind Spot or closing in (1.8s <= TTC < 3.5s)
    CRITICAL = 3    # Flashing Red: Imminent collision risk! (TTC < 1.8s or high closing speed)


class ThreatZone(IntEnum):
    NONE = 0
    LEFT_BLIND_SPOT = 1
    RIGHT_BLIND_SPOT = 2
    REAR_CENTER_CORRIDOR = 3


@dataclass
class VehicleThreatReport:
    track_id: int
    class_name: str
    threat_level: ThreatLevel
    threat_zone: ThreatZone
    estimated_distance_m: float
    relative_speed_kmh: float       # Positive = approaching bike, Negative = falling behind
    ttc_seconds: float              # Time to collision in seconds (inf if safe)
    bounding_box: List[int]
    threat_description: str


@dataclass
class ADASThreatSummary:
    highest_threat: ThreatLevel
    left_blind_spot_active: bool
    right_blind_spot_active: bool
    critical_collision_warning: bool
    minimum_ttc_seconds: float
    threat_count: int
    threat_reports: List[VehicleThreatReport]


# Real-world vehicle heights (in meters) for geometric distance estimation
NOMINAL_VEHICLE_HEIGHTS = {
    "car": 1.45,
    "truck": 2.85,
    "bus": 3.10,
    "motorcycle": 1.25,
    "bicycle": 1.10,
    "person": 1.70,
}


class TTCCalculator:
    """
    Computes Time-To-Collision and Blind Spot Threat Levels
    dynamically scaled by motorcycle road speed.
    """
    def __init__(
        self,
        camera_fov_v_deg: float = 65.0,  # Vertical Field of View of camera
        critical_ttc_thresh: float = 1.8, # Seconds to impact for CRITICAL alarm
        warning_ttc_thresh: float = 3.2,  # Seconds to impact for WARNING alarm
        blind_spot_dist_thresh: float = 7.5 # Meters for blind spot presence
    ):
        self.camera_fov_v_deg = camera_fov_v_deg
        self.critical_ttc_thresh = critical_ttc_thresh
        self.warning_ttc_thresh = warning_ttc_thresh
        self.blind_spot_dist_thresh = blind_spot_dist_thresh

    def assess_threats(
        self,
        tracked_vehicles: List[TrackedVehicle],
        frame_shape: Tuple[int, int],
        telemetry: TelemetryData
    ) -> ADASThreatSummary:
        frame_h, frame_w = frame_shape[:2]
        focal_length_px = (frame_h / 2.0) / math.tan(math.radians(self.camera_fov_v_deg / 2.0))

        reports: List[VehicleThreatReport] = []
        highest_threat = ThreatLevel.CLEAR
        left_bs_active = False
        right_bs_active = False
        critical_collision = False
        min_ttc = 99.0

        for track in tracked_vehicles:
            # 1. Estimate real-world distance via pinhole model
            nominal_height = NOMINAL_VEHICLE_HEIGHTS.get(track.class_name, 1.45)
            h_pixels = max(10, track.height)
            distance_m = (focal_length_px * nominal_height) / h_pixels
            distance_m = round(max(0.5, min(75.0, distance_m)), 1)
            track.estimated_distance_m = distance_m

            # 2. Estimate Relative Closing Speed
            # Using Optical Tau: TTC = h / (dh/dt)
            # Relative speed v_rel = distance / TTC
            tau = track.optical_tau
            if tau < 90.0 and tau > 0.1:
                rel_speed_ms = distance_m / tau
                rel_speed_kmh = rel_speed_ms * 3.6
                ttc = tau
            else:
                rel_speed_kmh = 0.0
                ttc = 99.0

            track.relative_speed_kmh = round(rel_speed_kmh, 1)

            # 3. Spatial Zone Identification
            norm_center_x = track.center[0] / frame_w
            zone = ThreatZone.NONE

            if norm_center_x <= 0.35:
                zone = ThreatZone.LEFT_BLIND_SPOT
            elif norm_center_x >= 0.65:
                zone = ThreatZone.RIGHT_BLIND_SPOT
            else:
                zone = ThreatZone.REAR_CENTER_CORRIDOR

            # 4. Threat Classification with Adaptive Context
            bike_speed = telemetry.speed_kmh
            threat = ThreatLevel.CLEAR
            desc = "Clear"

            # Context Rule 1: Bike is stationary or crawling (< 10 km/h) at a red light/junction
            if bike_speed < 10.0:
                # Any vehicle rapidly closing in on a stationary bike is critical
                if (ttc < self.critical_ttc_thresh and rel_speed_kmh > 8.0) or (rel_speed_kmh > 15.0 and distance_m < 25.0):
                    threat = ThreatLevel.CRITICAL
                    desc = f"Fast rear approach while stopped! (TTC: {ttc:.1f}s)"
                elif distance_m < 3.5:
                    threat = ThreatLevel.WARNING
                    desc = "Tailgater too close!"
                elif zone in (ThreatZone.LEFT_BLIND_SPOT, ThreatZone.RIGHT_BLIND_SPOT) and distance_m < self.blind_spot_dist_thresh:
                    threat = ThreatLevel.WARNING
                    desc = "Vehicle in blind spot"

            # Context Rule 2: Cruising / Highway Speeds
            else:
                # Active Blind Spot Detection
                if zone in (ThreatZone.LEFT_BLIND_SPOT, ThreatZone.RIGHT_BLIND_SPOT) and distance_m < self.blind_spot_dist_thresh:
                    threat = ThreatLevel.WARNING
                    desc = "Blind Spot alert"

                # Collision Vectoring (TTC)
                if ttc < self.critical_ttc_thresh and rel_speed_kmh > 10.0:
                    threat = ThreatLevel.CRITICAL
                    desc = f"CRITICAL! Collision risk in {ttc:.1f}s"
                elif ttc < self.warning_ttc_thresh and rel_speed_kmh > 8.0:
                    threat = max(threat, ThreatLevel.WARNING)
                    desc = f"Approaching ({rel_speed_kmh:.0f} km/h faster)"
                elif distance_m < 30.0 and threat == ThreatLevel.CLEAR:
                    threat = ThreatLevel.MONITORING
                    desc = f"Following at {distance_m:.0f}m"

            # Update zone flags
            if zone == ThreatZone.LEFT_BLIND_SPOT and threat >= ThreatLevel.WARNING:
                left_bs_active = True
            if zone == ThreatZone.RIGHT_BLIND_SPOT and threat >= ThreatLevel.WARNING:
                right_bs_active = True
            if threat == ThreatLevel.CRITICAL:
                critical_collision = True

            if ttc < min_ttc and rel_speed_kmh > 5.0:
                min_ttc = ttc

            highest_threat = max(highest_threat, threat)

            reports.append(
                VehicleThreatReport(
                    track_id=track.track_id,
                    class_name=track.class_name,
                    threat_level=threat,
                    threat_zone=zone,
                    estimated_distance_m=distance_m,
                    relative_speed_kmh=rel_speed_kmh,
                    ttc_seconds=round(ttc, 1),
                    bounding_box=list(track.box),
                    threat_description=desc
                )
            )

        return ADASThreatSummary(
            highest_threat=highest_threat,
            left_blind_spot_active=left_bs_active,
            right_blind_spot_active=right_bs_active,
            critical_collision_warning=critical_collision,
            minimum_ttc_seconds=min_ttc if min_ttc < 90.0 else -1.0,
            threat_count=len([r for r in reports if r.threat_level >= ThreatLevel.WARNING]),
            threat_reports=reports
        )
