"""
Indriyo - Core ADAS Pipeline Engine
Glues Stream Receiver, Telemetry, Vehicle Detector, Multi-Object Tracker,
TTC Assessment, Audio Alerts, and HUD Renderer into a unified, high-FPS pipeline.
"""

import time
import cv2
import numpy as np
from typing import Optional, Tuple, Callable

from indriyo_core.telemetry import BaseTelemetrySource, SimulatedTelemetry, TelemetryData
from indriyo_core.stream_receiver import StreamReceiver, MJPEGStreamReceiver, OpenCVStreamReceiver
from indriyo_core.detector import BaseDetector, AdaptiveVehicleDetector
from indriyo_core.tracker import MultiObjectVehicleTracker
from indriyo_core.ttc_calculator import TTCCalculator, ADASThreatSummary, ThreatLevel
from indriyo_core.hud_renderer import HUDRenderer
from indriyo_core.audio_alerts import AudioAlertDispatcher
from indriyo_core.synthetic_stream import SyntheticRearviewStream


class IndriyoEngine:
    """
    Main ADAS Coordinator for Indriyo.
    """
    def __init__(
        self,
        stream_receiver: StreamReceiver,
        telemetry_source: Optional[BaseTelemetrySource] = None,
        detector: Optional[BaseDetector] = None,
        enable_audio: bool = True,
        hud_width: int = 800,
        hud_height: int = 480
    ):
        self.stream_receiver = stream_receiver
        self.telemetry_source = telemetry_source or SimulatedTelemetry(base_speed_kmh=60.0)
        self.detector = detector or AdaptiveVehicleDetector()
        self.tracker = MultiObjectVehicleTracker(max_age=6, min_hits=2, iou_threshold=0.2)
        self.ttc_calculator = TTCCalculator()
        self.hud_renderer = HUDRenderer(target_width=hud_width, target_height=hud_height)
        self.audio_alerts = AudioAlertDispatcher(enable_sound=enable_audio)

        # Performance metrics
        self.fps = 0.0
        self.latency_ms = 0.0
        self._last_frame_time = time.time()
        self._frame_count = 0
        self._fps_timer = time.time()

        # Callbacks for mobile / web / external dashboards
        self.on_threat_updated: Optional[Callable[[ADASThreatSummary], None]] = None

    def process_step(self) -> Tuple[bool, Optional[np.ndarray], Optional[ADASThreatSummary]]:
        """
        Executes one full iteration of the ADAS pipeline:
        Fetch -> Detect -> Track -> TTC Assess -> Alert -> Render HUD
        """
        t0 = time.time()

        # 1. Fetch latest video frame
        ret, frame = self.stream_receiver.get_frame()
        if not ret or frame is None:
            return False, None, None

        # 2. Fetch active motorcycle telemetry (Speed, Heading, Throttle)
        telemetry = self.telemetry_source.get_telemetry()

        # 3. Object Detection (Vehicles)
        detections = self.detector.detect(frame)

        # 4. Multi-Object Tracking & Optical Expansion Vectoring
        tracked_vehicles = self.tracker.update(detections, timestamp=t0)

        # 5. Time-to-Collision & Blind Spot Assessment
        threat_summary = self.ttc_calculator.assess_threats(
            tracked_vehicles=tracked_vehicles,
            frame_shape=frame.shape[:2],
            telemetry=telemetry
        )

        # 6. Audio & Haptic Alert Dispatch
        self.audio_alerts.process_threat(threat_summary)

        # 7. Notify external subscribers
        if self.on_threat_updated:
            try:
                self.on_threat_updated(threat_summary)
            except Exception:
                pass

        # 8. Compute FPS & Latency
        t1 = time.time()
        self.latency_ms = (t1 - t0) * 1000.0

        self._frame_count += 1
        if t1 - self._fps_timer >= 0.5:
            self.fps = self._frame_count / (t1 - self._fps_timer)
            self._frame_count = 0
            self._fps_timer = t1

        # 9. Render Digital Mirror HUD Overlay
        annotated_hud = self.hud_renderer.render(
            frame=frame,
            threat_summary=threat_summary,
            telemetry=telemetry,
            fps=self.fps,
            latency_ms=self.latency_ms
        )

        return True, annotated_hud, threat_summary

    def close(self):
        """Releases all camera and telemetry resources."""
        self.stream_receiver.release()
        self.telemetry_source.close()
