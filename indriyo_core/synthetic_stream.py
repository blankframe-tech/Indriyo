"""
Indriyo - Synthetic Rearview Video & Scenario Generator
Generates dynamic, realistic motorcycle rear-camera feeds for headless testing,
benchmarking, and GUI simulation without requiring physical hardware.
"""

import math
import time
import cv2
import numpy as np
from typing import Tuple, List, Optional
from indriyo_core.detector import Detection
from indriyo_core.stream_receiver import StreamReceiver


class SyntheticVehicle:
    """A simulated vehicle in the motorcycle's rear zone."""
    def __init__(
        self,
        class_name: str,
        color_bgr: Tuple[int, int, int],
        initial_dist_m: float,
        relative_speed_kmh: float,
        lateral_offset: float,  # -1.0 (far left) to 1.0 (far right)
        behavior: str = "overtake"
    ):
        self.class_name = class_name
        self.color_bgr = color_bgr
        self.dist_m = initial_dist_m
        self.rel_speed_kmh = relative_speed_kmh
        self.lateral_offset = lateral_offset
        self.behavior = behavior
        self.initial_dist = initial_dist_m

    def update(self, dt: float):
        # Update distance based on relative speed
        # Positive relative speed means closing the distance
        speed_ms = self.rel_speed_kmh / 3.6
        self.dist_m -= speed_ms * dt

        if self.behavior == "overtake":
            if self.dist_m < 3.0:
                # Overtaking past the bike: reset far behind for cyclic simulation
                self.dist_m = self.initial_dist
        elif self.behavior == "hover_blindspot":
            # Hovers in blind spot between 4m and 7m
            if self.dist_m < 4.5:
                self.rel_speed_kmh = -2.0
            elif self.dist_m > 7.0:
                self.rel_speed_kmh = 3.0
        elif self.behavior == "tailgater":
            if self.dist_m < 2.5:
                self.dist_m = self.initial_dist


class SyntheticRearviewStream(StreamReceiver):
    """
    Renders high-quality synthetic motorcycle rear camera frames
    complete with asphalt perspective, lane lines, dynamic vehicle 3D perspective,
    taillights, and camera vibrations.
    """
    def __init__(
        self,
        width: int = 800,
        height: int = 480,
        scenario: str = "tailgater"
    ):
        self.width = width
        self.height = height
        self.scenario = scenario
        self.start_time = time.time()
        self.last_update = time.time()
        self.road_phase = 0.0

        self.vehicles: List[SyntheticVehicle] = []
        self._init_scenario(scenario)

    def _init_scenario(self, scenario: str):
        self.vehicles.clear()
        if scenario == "tailgater":
            # Fast approaching sedan directly behind
            self.vehicles.append(
                SyntheticVehicle("car", (40, 40, 200), initial_dist_m=45.0, relative_speed_kmh=35.0, lateral_offset=0.0, behavior="tailgater")
            )
        elif scenario == "blindspot":
            # Vehicle lingering in left blind spot
            self.vehicles.append(
                SyntheticVehicle("car", (30, 160, 220), initial_dist_m=12.0, relative_speed_kmh=8.0, lateral_offset=-0.65, behavior="hover_blindspot")
            )
        elif scenario == "dual_overtake":
            # Car in right blind spot, motorcycle on left
            self.vehicles.append(
                SyntheticVehicle("car", (50, 50, 180), initial_dist_m=35.0, relative_speed_kmh=25.0, lateral_offset=0.6, behavior="overtake")
            )
            self.vehicles.append(
                SyntheticVehicle("motorcycle", (200, 120, 30), initial_dist_m=20.0, relative_speed_kmh=15.0, lateral_offset=-0.55, behavior="overtake")
            )
        else: # "dhaka_traffic"
            self.vehicles.append(
                SyntheticVehicle("bus", (30, 180, 50), initial_dist_m=30.0, relative_speed_kmh=18.0, lateral_offset=0.1, behavior="overtake")
            )
            self.vehicles.append(
                SyntheticVehicle("motorcycle", (180, 80, 40), initial_dist_m=10.0, relative_speed_kmh=6.0, lateral_offset=-0.65, behavior="hover_blindspot")
            )

    def set_scenario(self, scenario: str):
        self.scenario = scenario
        self._init_scenario(scenario)

    def get_ground_truth_detections(self) -> List[Detection]:
        """Returns exact bounding boxes of synthetic vehicles for test validation."""
        detections = []
        h, w = self.height, self.width
        vanish_y = int(h * 0.38)
        focal = h * 0.9

        for v in self.vehicles:
            if v.dist_m <= 0.8:
                continue

            # Scale based on distance
            scale = focal / v.dist_m
            car_w = int(1.8 * scale)
            car_h = int(1.4 * scale)

            # Screen center
            center_x = int(w * 0.5 + v.lateral_offset * (w * 0.45) * (1.0 - (v.dist_m / 60.0)))
            center_y = int(vanish_y + (h - vanish_y) * (1.0 / (1.0 + v.dist_m * 0.12)))

            x1 = max(0, center_x - car_w // 2)
            y1 = max(vanish_y, center_y - car_h)
            x2 = min(w, center_x + car_w // 2)
            y2 = min(h - 10, center_y)

            if x2 > x1 + 10 and y2 > y1 + 10:
                cls_id = 7 if v.class_name == "truck" or v.class_name == "bus" else (3 if v.class_name == "motorcycle" else 2)
                detections.append(
                    Detection(
                        box=(x1, y1, x2, y2),
                        confidence=0.98,
                        class_name=v.class_name,
                        class_id=cls_id
                    )
                )
        return detections

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        now = time.time()
        dt = max(0.001, min(0.1, now - self.last_update))
        self.last_update = now

        # Update synthetic vehicles
        for v in self.vehicles:
            v.update(dt)

        w, h = self.width, self.height
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # 1. Sky & Dusk Ambient Gradient
        vanish_y = int(h * 0.38)
        for y in range(vanish_y):
            progress = y / float(vanish_y)
            # Dusk gradient: deep slate blue to warm amber horizon
            b = int(45 * (1 - progress) + 30 * progress)
            g = int(25 * (1 - progress) + 40 * progress)
            r = int(60 * (1 - progress) + 80 * progress)
            frame[y, :] = (b, g, r)

        # 2. Road plane
        for y in range(vanish_y, h):
            progress = (y - vanish_y) / float(h - vanish_y)
            # Road asphalt gets darker and texture increases
            road_val = int(28 + progress * 20)
            frame[y, :] = (road_val, road_val + 2, road_val + 4)

        # 3. Dynamic Animated Lane Markings (moving toward camera)
        self.road_phase = (self.road_phase + dt * 4.0) % 1.0
        dash_count = 12
        for i in range(dash_count):
            rel_pos = ((i / float(dash_count)) + self.road_phase) % 1.0
            cur_y = int(vanish_y + (h - vanish_y) * (rel_pos ** 1.8))
            next_y = int(vanish_y + (h - vanish_y) * (min(1.0, rel_pos + 0.04) ** 1.8))
            dash_w = max(2, int(rel_pos * 12))

            # Left lane dash
            lx1 = int(w * 0.5 - (w * 0.35) * rel_pos)
            cv2.line(frame, (lx1, cur_y), (lx1, next_y), (140, 140, 140), dash_w)

            # Right lane dash
            rx1 = int(w * 0.5 + (w * 0.35) * rel_pos)
            cv2.line(frame, (rx1, cur_y), (rx1, next_y), (140, 140, 140), dash_w)

        # 4. Render Synthetic Vehicles
        focal = h * 0.9
        # Sort vehicles back-to-front so nearest vehicles occlude further ones
        sorted_vehicles = sorted(self.vehicles, key=lambda v: v.dist_m, reverse=True)

        for v in sorted_vehicles:
            if v.dist_m <= 0.8:
                continue

            scale = focal / v.dist_m
            car_w = int(1.8 * scale)
            car_h = int(1.4 * scale)

            center_x = int(w * 0.5 + v.lateral_offset * (w * 0.45) * (1.0 - (v.dist_m / 60.0)))
            center_y = int(vanish_y + (h - vanish_y) * (1.0 / (1.0 + v.dist_m * 0.12)))

            x1 = max(0, center_x - car_w // 2)
            y1 = max(vanish_y, center_y - car_h)
            x2 = min(w, center_x + car_w // 2)
            y2 = min(h - 10, center_y)

            if x2 > x1 + 8 and y2 > y1 + 8:
                # Vehicle chassis
                cv2.rectangle(frame, (x1, y1 + int(car_h * 0.35)), (x2, y2), v.color_bgr, -1)
                
                # Windshield / cabin
                cabin_inset = max(2, int(car_w * 0.15))
                cv2.rectangle(frame, (x1 + cabin_inset, y1), (x2 - cabin_inset, y1 + int(car_h * 0.4)), (20, 20, 25), -1)

                # Headlights (front facing camera as vehicle approaches motorcycle)
                hl_y = int(y2 - car_h * 0.25)
                hl_r = max(2, int(car_w * 0.08))
                # Left headlight
                cv2.circle(frame, (x1 + int(car_w * 0.2), hl_y), hl_r, (255, 255, 220), -1)
                # Right headlight
                cv2.circle(frame, (x2 - int(car_w * 0.2), hl_y), hl_r, (255, 255, 220), -1)

                # Headlight beams / glow
                if car_w > 40:
                    overlay = frame.copy()
                    cv2.circle(overlay, (x1 + int(car_w * 0.2), hl_y), hl_r * 3, (180, 220, 255), -1)
                    cv2.circle(overlay, (x2 - int(car_w * 0.2), hl_y), hl_r * 3, (180, 220, 255), -1)
                    cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

                # Grille & bumper
                cv2.rectangle(frame, (x1 + int(car_w * 0.25), hl_y - 2), (x2 - int(car_w * 0.25), hl_y + 8), (15, 15, 15), -1)

        # 5. Mirror Horizontal Flip (As requested in PRD: realistic digital rearview mirror)
        frame = cv2.flip(frame, 1)

        return True, frame
