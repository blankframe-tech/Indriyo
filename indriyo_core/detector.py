"""
Indriyo - Vehicle Object Detection Subsystem
Detects cars, motorcycles, trucks, buses, and cyclists in the rear camera feed.
Includes fallback detectors so the system can run on any platform (Pi, Mac, Linux, PC)
without requiring a GPU or massive PyTorch installations.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import cv2
import numpy as np


@dataclass
class Detection:
    box: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    class_name: str
    class_id: int

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


VEHICLE_CLASSES = {"car", "motorcycle", "truck", "bus", "bicycle", "person"}


class BaseDetector:
    def detect(self, frame: np.ndarray) -> List[Detection]:
        raise NotImplementedError


class YOLOv8Detector(BaseDetector):
    """
    YOLOv8 Detector using Ultralytics or ONNX Runtime.
    Filters exclusively for road vehicle classes to prevent false alarms.
    """
    COCO_CLASSES = {
        0: "person",
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }

    def __init__(self, model_path: str = "yolov8n.pt", conf_thresh: float = 0.35):
        self.conf_thresh = conf_thresh
        self.model = None
        self._load_model(model_path)

    def _load_model(self, model_path: str):
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
        except Exception:
            self.model = None

    def detect(self, frame: np.ndarray) -> List[Detection]:
        if self.model is None or frame is None:
            return []

        results = self.model(frame, verbose=False, conf=self.conf_thresh)
        detections = []

        for r in results:
            boxes = r.boxes
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                if cls_id in self.COCO_CLASSES:
                    conf = float(boxes.conf[i].item())
                    xyxy = boxes.xyxy[i].cpu().numpy().astype(int)
                    detections.append(
                        Detection(
                            box=(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])),
                            confidence=conf,
                            class_name=self.COCO_CLASSES[cls_id],
                            class_id=cls_id
                        )
                    )
        return detections


class VisionHeuristicDetector(BaseDetector):
    """
    Lightweight, ultra-fast Computer Vision detector that identifies
    vehicle silhouettes, headlight pairs, and high-contrast rear windshields/bumpers.
    Runs at 60+ FPS on any low-power ARM CPU without neural network overhead.
    """
    def __init__(self, min_area: int = 1500, max_area: int = 250000):
        self.min_area = min_area
        self.max_area = max_area

    def detect(self, frame: np.ndarray) -> List[Detection]:
        if frame is None:
            return []

        h, w = frame.shape[:2]
        # Restrict search to lower 75% of frame (the road plane)
        road_roi_y = int(h * 0.25)
        roi = frame[road_roi_y:, :]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Sobel vertical edge detection (identifies vehicle flanks and rear outlines)
        sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        abs_sobel64f = np.absolute(sobelx)
        sobel_8u = np.uint8(abs_sobel64f)
        _, thresh = cv2.threshold(sobel_8u, 40, 255, cv2.THRESH_BINARY)

        # Morphological closing to group vehicle body parts
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 7))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_area <= area <= self.max_area:
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = cw / float(ch)

                # Vehicles viewed from behind typically have aspect ratio 0.6 to 2.4
                if 0.5 <= aspect_ratio <= 3.0 and ch > 30 and cw > 35:
                    global_y1 = y + road_roi_y
                    global_y2 = global_y1 + ch
                    global_x1 = x
                    global_x2 = x + cw

                    # Classify based on size and aspect ratio
                    if aspect_ratio < 0.9 and ch > 80:
                        class_name = "motorcycle"
                        cls_id = 3
                    elif area > 35000 or (cw > w * 0.4):
                        class_name = "truck"
                        cls_id = 7
                    else:
                        class_name = "car"
                        cls_id = 2

                    conf = min(0.95, 0.45 + (area / self.max_area) * 0.5)
                    detections.append(
                        Detection(
                            box=(global_x1, global_y1, global_x2, global_y2),
                            confidence=conf,
                            class_name=class_name,
                            class_id=cls_id
                        )
                    )

        # Non-maximum suppression to eliminate overlapping boxes
        return self._apply_nms(detections, iou_thresh=0.3)

    def _apply_nms(self, detections: List[Detection], iou_thresh: float) -> List[Detection]:
        if not detections:
            return []

        boxes = [d.box for d in detections]
        confs = [d.confidence for d in detections]

        indices = cv2.dnn.NMSBoxes(
            bboxes=[[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in boxes],
            scores=confs,
            score_threshold=0.3,
            nms_threshold=iou_thresh
        )

        if len(indices) == 0:
            return []

        filtered = []
        for idx in indices.flatten():
            filtered.append(detections[idx])
        return filtered


class AdaptiveVehicleDetector(BaseDetector):
    """
    Primary detector for Indriyo.
    Uses YOLOv8 if installed, else gracefully falls back to VisionHeuristicDetector.
    """
    def __init__(self, model_path: Optional[str] = None):
        self.active_backend = "heuristic"
        self.detector = VisionHeuristicDetector()

        try:
            import ultralytics
            if model_path:
                self.detector = YOLOv8Detector(model_path)
                self.active_backend = "yolov8"
        except ImportError:
            pass

    def detect(self, frame: np.ndarray) -> List[Detection]:
        return self.detector.detect(frame)
