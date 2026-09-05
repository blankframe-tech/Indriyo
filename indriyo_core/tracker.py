"""
Indriyo - Real-Time Multi-Object Vehicle Tracker
Tracks vehicles over time to compute approach velocities, bounding box expansion rates,
and vector trajectories for Time-to-Collision (TTC) calculations.
"""

import time
import numpy as np
from typing import List, Tuple, Dict, Optional
from indriyo_core.detector import Detection


def calculate_iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
    """Computes Intersection over Union (IoU) between two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter_width = max(0, xB - xA)
    inter_height = max(0, yB - yA)
    inter_area = inter_width * inter_height

    boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    union_area = float(boxA_area + boxB_area - inter_area)
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class TrackedVehicle:
    """Represents an active vehicle tracked across video frames."""
    def __init__(self, track_id: int, initial_detection: Detection, timestamp: float):
        self.track_id = track_id
        self.class_name = initial_detection.class_name
        self.class_id = initial_detection.class_id
        self.confidence = initial_detection.confidence

        # Bounding box: [x1, y1, x2, y2]
        self.box = list(initial_detection.box)
        self.history: List[Tuple[float, List[int]]] = [(timestamp, list(initial_detection.box))]

        self.hits = 1
        self.time_since_update = 0
        self.first_seen = timestamp
        self.last_seen = timestamp

        # Dynamic metrics
        self.expansion_rate = 0.0       # Pixel height growth rate (pixels / sec)
        self.area_expansion_rate = 0.0  # Area growth rate
        self.optical_tau = 99.0         # Optical Tau = height / expansion_rate
        self.estimated_distance_m = 25.0 # Estimated distance in meters
        self.relative_speed_kmh = 0.0   # Relative approach speed (positive = approaching)

    @property
    def width(self) -> int:
        return max(1, self.box[2] - self.box[0])

    @property
    def height(self) -> int:
        return max(1, self.box[3] - self.box[1])

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.box[0] + self.box[2]) / 2.0, (self.box[1] + self.box[3]) / 2.0)

    def update(self, detection: Detection, timestamp: float):
        self.last_seen = timestamp
        self.hits += 1
        self.time_since_update = 0
        self.confidence = 0.7 * self.confidence + 0.3 * detection.confidence
        self.class_name = detection.class_name

        # Smooth box with EMA (Exponential Moving Average)
        alpha = 0.65
        self.box = [
            int(alpha * detection.box[0] + (1 - alpha) * self.box[0]),
            int(alpha * detection.box[1] + (1 - alpha) * self.box[1]),
            int(alpha * detection.box[2] + (1 - alpha) * self.box[2]),
            int(alpha * detection.box[3] + (1 - alpha) * self.box[3]),
        ]

        self.history.append((timestamp, list(self.box)))
        # Keep recent 2.0 seconds of history
        cutoff = timestamp - 2.0
        self.history = [h for h in self.history if h[0] >= cutoff]

        self._compute_kinematics(timestamp)

    def _compute_kinematics(self, current_time: float):
        """Computes rate of expansion (Tau) over sliding temporal window."""
        if len(self.history) < 3:
            return

        # Compare current state with state ~0.25 - 0.5 seconds ago for stable derivative
        target_time = current_time - 0.35
        # Find closest past state
        past_state = min(self.history[:-1], key=lambda x: abs(x[0] - target_time))
        dt = current_time - past_state[0]

        if dt > 0.05:
            past_box = past_state[1]
            past_h = max(1, past_box[3] - past_box[1])
            curr_h = self.height

            # Height expansion rate (dh/dt)
            dh_dt = (curr_h - past_h) / dt
            self.expansion_rate = 0.6 * self.expansion_rate + 0.4 * dh_dt

            # Optical Tau = h / (dh/dt)
            if self.expansion_rate > 0.5:
                raw_tau = curr_h / self.expansion_rate
                self.optical_tau = max(0.1, min(99.0, raw_tau))
            else:
                self.optical_tau = 99.0  # Object is pacing or falling behind

    def mark_missed(self):
        self.time_since_update += 1


class MultiObjectVehicleTracker:
    """
    Associates incoming detections with persistent tracked vehicle trajectories.
    """
    def __init__(self, max_age: int = 8, min_hits: int = 2, iou_threshold: float = 0.25):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: Dict[int, TrackedVehicle] = {}
        self._next_id = 1

    def update(self, detections: List[Detection], timestamp: Optional[float] = None) -> List[TrackedVehicle]:
        if timestamp is None:
            timestamp = time.time()

        matched_tracks = set()
        matched_detections = set()

        # Compute IoU cost matrix
        if self.tracks and detections:
            track_ids = list(self.tracks.keys())
            iou_matrix = np.zeros((len(track_ids), len(detections)), dtype=np.float32)

            for i, tid in enumerate(track_ids):
                for j, det in enumerate(detections):
                    iou_matrix[i, j] = calculate_iou(tuple(self.tracks[tid].box), det.box)

            # Greedy Hungarian-style matching
            while True:
                max_val = np.max(iou_matrix) if iou_matrix.size > 0 else 0.0
                if max_val < self.iou_threshold:
                    break
                row, col = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                tid = track_ids[row]
                self.tracks[tid].update(detections[col], timestamp)
                matched_tracks.add(tid)
                matched_detections.add(col)
                # Invalidate matched row and column
                iou_matrix[row, :] = -1
                iou_matrix[:, col] = -1

        # Mark unmatched tracks as missed
        for tid, track in list(self.tracks.items()):
            if tid not in matched_tracks:
                track.mark_missed()
                if track.time_since_update > self.max_age:
                    del self.tracks[tid]

        # Register new detections as new tracks
        for j, det in enumerate(detections):
            if j not in matched_detections:
                new_track = TrackedVehicle(self._next_id, det, timestamp)
                self.tracks[self._next_id] = new_track
                self._next_id += 1

        # Return confirmed active tracks
        return [t for t in self.tracks.values() if t.hits >= self.min_hits and t.time_since_update == 0]
