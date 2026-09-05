"""
Indriyo - High-Performance Digital Rearview Mirror HUD Renderer
Renders high-contrast peripheral warning borders (Amber / Flashing Red),
tactical target brackets, and real-time telemetry overlays.
"""

import time
import math
import cv2
import numpy as np
from typing import Tuple, List, Optional
from indriyo_core.ttc_calculator import ThreatLevel, ThreatZone, ADASThreatSummary, VehicleThreatReport
from indriyo_core.telemetry import TelemetryData


# Color Palette (BGR for OpenCV)
COLOR_CLEAR_GREEN  = (50, 215, 75)      # iOS / Neon Emerald Green
COLOR_WARNING_AMBER = (0, 165, 255)     # Glowing Amber / Orange
COLOR_CRITICAL_RED  = (30, 30, 255)     # Rapid Flashing Laser Red
COLOR_CYAN_TECH     = (255, 200, 0)     # Cockpit Tech Cyan
COLOR_DARK_GLASS    = (20, 20, 24)      # Translucent dark backing
COLOR_WHITE         = (255, 255, 255)
COLOR_TEXT_DIM      = (180, 180, 180)


class HUDRenderer:
    """
    Overlays the Indriyo digital rearview mirror HUD onto raw camera frames.
    """
    def __init__(self, target_width: int = 800, target_height: int = 480):
        self.target_width = target_width
        self.target_height = target_height
        self._flash_state = False
        self._last_flash_toggle = time.time()
        self.flash_frequency_hz = 5.0  # 5 flashes per second for critical threats

    def render(
        self,
        frame: np.ndarray,
        threat_summary: ADASThreatSummary,
        telemetry: TelemetryData,
        fps: float = 30.0,
        latency_ms: float = 18.5
    ) -> np.ndarray:
        # Resize to HUD resolution if needed
        h, w = frame.shape[:2]
        if (w, h) != (self.target_width, self.target_height):
            frame = cv2.resize(frame, (self.target_width, self.target_height))
            h, w = self.target_height, self.target_width

        # Update flash state for critical alerts
        now = time.time()
        if now - self._last_flash_toggle >= (1.0 / (self.flash_frequency_hz * 2.0)):
            self._flash_state = not self._flash_state
            self._last_flash_toggle = now

        output = frame.copy()

        # 1. Render Blind Spot Zone Division Guides
        self._draw_zone_guidelines(output, w, h)

        # 2. Render Tracked Vehicle Target Boxes
        for report in threat_summary.threat_reports:
            self._draw_target_box(output, report, w, h)

        # 3. Render Peripheral Perimeter Alert Border (The Core PRD UX)
        self._draw_peripheral_border(output, threat_summary, w, h)

        # 4. Render Top Telemetry Status Header
        self._draw_telemetry_header(output, threat_summary, telemetry, w, h, fps, latency_ms)

        # 5. Render Bottom Threat Banner
        self._draw_bottom_status(output, threat_summary, telemetry, w, h)

        return output

    def _draw_zone_guidelines(self, img: np.ndarray, w: int, h: int):
        """Draws subtle dashed guidelines demarcating left and right blind spots."""
        left_x = int(w * 0.35)
        right_x = int(w * 0.65)
        horizon_y = int(h * 0.35)

        # Subtle dark road grid
        dash_len = 12
        for y in range(horizon_y, h, dash_len * 2):
            cv2.line(img, (left_x, y), (left_x, min(h, y + dash_len)), (80, 80, 80), 1, cv2.LINE_AA)
            cv2.line(img, (right_x, y), (right_x, min(h, y + dash_len)), (80, 80, 80), 1, cv2.LINE_AA)

    def _draw_target_box(self, img: np.ndarray, report: VehicleThreatReport, w: int, h: int):
        """Draws sleek corner brackets and floating info cards."""
        box = report.bounding_box
        x1, y1, x2, y2 = box

        # Select color based on threat level
        if report.threat_level == ThreatLevel.CRITICAL:
            color = COLOR_CRITICAL_RED if self._flash_state else (100, 100, 255)
            thickness = 3
        elif report.threat_level == ThreatLevel.WARNING:
            color = COLOR_WARNING_AMBER
            thickness = 2
        elif report.threat_level == ThreatLevel.MONITORING:
            color = COLOR_CYAN_TECH
            thickness = 1
        else:
            color = COLOR_CLEAR_GREEN
            thickness = 1

        bw = x2 - x1
        bh = y2 - y1
        corner_len = max(8, min(24, int(min(bw, bh) * 0.25)))

        # Tactical corner brackets
        # Top-Left
        cv2.line(img, (x1, y1), (x1 + corner_len, y1), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1, y1), (x1, y1 + corner_len), color, thickness, cv2.LINE_AA)
        # Top-Right
        cv2.line(img, (x2, y1), (x2 - corner_len, y1), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x2, y1), (x2, y1 + corner_len), color, thickness, cv2.LINE_AA)
        # Bottom-Left
        cv2.line(img, (x1, y2), (x1 + corner_len, y2), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1, y2), (x1, y2 - corner_len), color, thickness, cv2.LINE_AA)
        # Bottom-Right
        cv2.line(img, (x2, y2), (x2 - corner_len, y2), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x2, y2), (x2, y2 - corner_len), color, thickness, cv2.LINE_AA)

        # Distance & Threat Badge
        badge_text = f"{report.class_name.upper()} | {report.estimated_distance_m:.1f}m"
        if report.threat_level == ThreatLevel.CRITICAL:
            badge_text += f" | TTC {report.ttc_seconds:.1f}s!"
        elif report.threat_level == ThreatLevel.WARNING:
            if report.threat_zone in (ThreatZone.LEFT_BLIND_SPOT, ThreatZone.RIGHT_BLIND_SPOT):
                badge_text += " | BLIND SPOT"
            else:
                badge_text += f" | +{report.relative_speed_kmh:.0f}km/h"

        badge_y = max(24, y1 - 8)
        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)

        # Badge background pill
        cv2.rectangle(img, (x1, badge_y - th - 4), (x1 + tw + 10, badge_y + 2), COLOR_DARK_GLASS, -1)
        cv2.rectangle(img, (x1, badge_y - th - 4), (x1 + tw + 10, badge_y + 2), color, 1)
        cv2.putText(img, badge_text, (x1 + 5, badge_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

    def _draw_peripheral_border(self, img: np.ndarray, threat_summary: ADASThreatSummary, w: int, h: int):
        """
        Draws the signature Indriyo peripheral awareness border:
        - Amber solid border on left/right for Blind Spot presence
        - Flashing Crimson Red border for critical collision hazards
        - Subtle green/stealth when clear
        """
        border_thickness = 12

        if threat_summary.highest_threat == ThreatLevel.CRITICAL:
            if self._flash_state:
                # Full red alert strobe
                cv2.rectangle(img, (0, 0), (w, h), COLOR_CRITICAL_RED, border_thickness)
                # Corner emergency triangles
                cv2.putText(img, "! COLLISION RISK !", (w // 2 - 140, 50),
                            cv2.FONT_HERSHEY_DUPLEX, 0.85, COLOR_CRITICAL_RED, 2, cv2.LINE_AA)
        elif threat_summary.highest_threat == ThreatLevel.WARNING:
            # Active amber border on threat side(s)
            if threat_summary.left_blind_spot_active:
                cv2.line(img, (0, 0), (0, h), COLOR_WARNING_AMBER, border_thickness)
                cv2.line(img, (0, 0), (int(w * 0.35), 0), COLOR_WARNING_AMBER, border_thickness)
                cv2.line(img, (0, h), (int(w * 0.35), h), COLOR_WARNING_AMBER, border_thickness)
            if threat_summary.right_blind_spot_active:
                cv2.line(img, (w - 1, 0), (w - 1, h), COLOR_WARNING_AMBER, border_thickness)
                cv2.line(img, (w - int(w * 0.35), 0), (w - 1, 0), COLOR_WARNING_AMBER, border_thickness)
                cv2.line(img, (w - int(w * 0.35), h), (w - 1, h), COLOR_WARNING_AMBER, border_thickness)
            if not threat_summary.left_blind_spot_active and not threat_summary.right_blind_spot_active:
                # Center warning
                cv2.rectangle(img, (0, 0), (w, h), COLOR_WARNING_AMBER, border_thickness // 2)
        else:
            # Subtle green border top/bottom
            cv2.line(img, (0, 0), (w, 0), (30, 100, 30), 2)
            cv2.line(img, (0, h - 1), (w, h - 1), (30, 100, 30), 2)

    def _draw_telemetry_header(
        self,
        img: np.ndarray,
        threat_summary: ADASThreatSummary,
        telemetry: TelemetryData,
        w: int,
        h: int,
        fps: float,
        latency_ms: float
    ):
        """Top HUD banner showing speed, active mode, and edge stats."""
        # Top gradient bar
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, 38), (10, 12, 16), -1)
        cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)

        # Brand mark
        cv2.putText(img, "INDRIYO", (16, 25), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "ADAS", (105, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_CYAN_TECH, 1, cv2.LINE_AA)

        # Bike Road Speed
        speed_str = f"{telemetry.speed_kmh:.0f} KM/H"
        cv2.putText(img, speed_str, (w // 2 - 40, 26), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 1, cv2.LINE_AA)

        # Edge stats
        stats_str = f"{fps:.0f} FPS | {latency_ms:.0f}ms"
        cv2.putText(img, stats_str, (w - 140, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_TEXT_DIM, 1, cv2.LINE_AA)

    def _draw_bottom_status(
        self,
        img: np.ndarray,
        threat_summary: ADASThreatSummary,
        telemetry: TelemetryData,
        w: int,
        h: int
    ):
        """Bottom HUD banner with status pill."""
        overlay = img.copy()
        cv2.rectangle(overlay, (0, h - 34), (w, h), (10, 12, 16), -1)
        cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)

        # Threat state indicator
        if threat_summary.highest_threat == ThreatLevel.CRITICAL:
            text = "CRITICAL WARNING: RAPID APPROACH"
            color = COLOR_CRITICAL_RED
        elif threat_summary.highest_threat == ThreatLevel.WARNING:
            text = "WARNING: BLIND SPOT OCCUPIED"
            color = COLOR_WARNING_AMBER
        elif threat_summary.highest_threat == ThreatLevel.MONITORING:
            text = "MONITORING: REAR CLEAR"
            color = COLOR_CYAN_TECH
        else:
            text = "SYSTEM READY - ALL CLEAR"
            color = COLOR_CLEAR_GREEN

        cv2.circle(img, (24, h - 17), 6, color, -1, cv2.LINE_AA)
        cv2.putText(img, text, (40, h - 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

        # Telemetry source badge
        src_text = f"SOURCE: {telemetry.source.upper()}"
        cv2.putText(img, src_text, (w - 160, h - 13), cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_TEXT_DIM, 1, cv2.LINE_AA)
