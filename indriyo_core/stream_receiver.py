"""
Indriyo - Multi-Source Video Stream Receiver
Receives MJPEG streams from ESP32-CAMs, USB webcams, or video files.
Runs in a background thread to prevent buffer latency.
"""

import cv2
import numpy as np
import threading
import time
import urllib.request
from typing import Optional, Tuple


class StreamReceiver:
    """Base class for video frame sources."""
    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        raise NotImplementedError

    def release(self):
        pass


class MJPEGStreamReceiver(StreamReceiver):
    """
    High-speed, zero-lag MJPEG stream client for ESP32-CAM.
    Decodes multipart/x-mixed-replace JPEG streams over HTTP.
    Uses a background worker thread with a 1-frame buffer to drop
    stale frames and guarantee the lowest possible latency for ADAS.
    """
    def __init__(self, url: str, reconnect_delay: float = 1.0):
        self.url = url
        self.reconnect_delay = reconnect_delay
        self._latest_frame = None
        self._running = True
        self._lock = threading.Lock()
        self._connected = False
        self._fps = 0.0
        self._frame_count = 0
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        while self._running:
            try:
                req = urllib.request.Request(self.url, headers={"User-Agent": "Indriyo-ADAS-Client"})
                stream = urllib.request.urlopen(req, timeout=5.0)
                bytes_buffer = bytes()
                self._connected = True
                last_fps_calc = time.time()
                frames_in_second = 0

                while self._running:
                    chunk = stream.read(4096)
                    if not chunk:
                        break
                    bytes_buffer += chunk

                    # Search for JPEG start (0xFFD8) and end (0xFFD9) markers
                    a = bytes_buffer.find(b'\xff\xd8')
                    b = bytes_buffer.find(b'\xff\xd9')
                    if a != -1 and b != -1 and b > a:
                        jpg_data = bytes_buffer[a:b+2]
                        bytes_buffer = bytes_buffer[b+2:]

                        # Decode image from buffer
                        frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            with self._lock:
                                self._latest_frame = frame
                            self._frame_count += 1
                            frames_in_second += 1

                            now = time.time()
                            if now - last_fps_calc >= 1.0:
                                self._fps = frames_in_second / (now - last_fps_calc)
                                frames_in_second = 0
                                last_fps_calc = now

            except Exception:
                self._connected = False
                time.sleep(self.reconnect_delay)

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self._lock:
            if self._latest_frame is not None:
                return True, self._latest_frame.copy()
            return False, None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def fps(self) -> float:
        return self._fps

    def release(self):
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)


class OpenCVStreamReceiver(StreamReceiver):
    """
    Standard OpenCV video capture for USB webcams, CSI cameras, or video files.
    """
    def __init__(self, source, loop: bool = True):
        # source can be integer (webcam index 0) or file path / RTSP URL
        self.source = source
        self.loop = loop
        self.cap = cv2.VideoCapture(source)
        self._fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.cap.isOpened():
            return False, None

        ret, frame = self.cap.read()
        if not ret and self.loop and isinstance(self.source, str):
            # Rewind video file
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        return ret, frame

    @property
    def fps(self) -> float:
        return self._fps

    def release(self):
        if self.cap:
            self.cap.release()


class DualCameraStitcher(StreamReceiver):
    """
    Ingests both Left and Right ESP32-CAM streams and stitches them
    side-by-side or composites them into a panoramic 180° rearview feed.
    """
    def __init__(self, left_source: StreamReceiver, right_source: StreamReceiver):
        self.left_source = left_source
        self.right_source = right_source

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        ret_l, frame_l = self.left_source.get_frame()
        ret_r, frame_r = self.right_source.get_frame()

        if not ret_l and not ret_r:
            return False, None
        
        # If one frame is missing, create a placeholder
        if ret_l and not ret_r:
            h, w = frame_l.shape[:2]
            frame_r = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.putText(frame_r, "RIGHT CAM OFFLINE", (20, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        elif ret_r and not ret_l:
            h, w = frame_r.shape[:2]
            frame_l = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.putText(frame_l, "LEFT CAM OFFLINE", (20, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Match heights
        h_l, w_l = frame_l.shape[:2]
        h_r, w_r = frame_r.shape[:2]
        target_h = min(h_l, h_r)
        
        if h_l != target_h:
            frame_l = cv2.resize(frame_l, (int(w_l * (target_h / h_l)), target_h))
        if h_r != target_h:
            frame_r = cv2.resize(frame_r, (int(w_r * (target_h / h_r)), target_h))

        # Horizontal stitch: Left on left half, Right on right half
        stitched = np.hstack([frame_l, frame_r])
        return True, stitched

    def release(self):
        self.left_source.release()
        self.right_source.release()
