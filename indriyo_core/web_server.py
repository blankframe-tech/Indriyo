"""
Indriyo - Self-Hosted Real-Time Web Stream Server
Streams processed ADAS rearview HUD frames over HTTP/MJPEG to any
browser, phone, or dashboard mounted on the motorcycle over local Wi-Fi.
Zero external dependencies (uses standard library http.server).
"""

import http.server
import socketserver
import threading
import time
import json
import cv2
import numpy as np
from typing import Optional
from indriyo_core.ttc_calculator import ThreatLevel


# Boundary delimiter for multipart MJPEG stream
STREAM_BOUNDARY = "indriyo_mjpeg_stream_boundary"


HTML_COCKPIT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Indriyo Cockpit HUD Mirror</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #000;
      color: #fff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }
    .hud-shell {
      position: relative;
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
      background: #05070a;
    }
    .stream-feed {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border: 4px solid #1a2230;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .fullscreen-btn {
      position: absolute;
      top: 16px;
      right: 16px;
      background: rgba(10, 14, 22, 0.75);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #fff;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      z-index: 10;
    }
  </style>
</head>
<body>
  <div class="hud-shell">
    <button class="fullscreen-btn" onclick="toggleFullscreen()">⛶ FULLSCREEN</button>
    <img id="mirrorFeed" class="stream-feed" src="/stream" alt="Indriyo Live ADAS Mirror">
  </div>

  <script>
    function toggleFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {});
      } else {
        document.exitFullscreen().catch(err => {});
      }
    }
  </script>
</body>
</html>
"""


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class ADASStreamServer:
    """
    Hosts the live ADAS stream and digital mirror web app.
    """
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self._latest_jpeg: Optional[bytes] = None
        self._latest_threat_json: str = "{}"
        self._lock = threading.Lock()
        self._server: Optional[ThreadedHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def update_frame(self, frame: np.ndarray, threat_summary=None, telemetry=None):
        """Encodes frame to JPEG and updates broadcast cache."""
        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            with self._lock:
                self._latest_jpeg = jpeg.tobytes()
                if threat_summary:
                    self._latest_threat_json = json.dumps({
                        "highest_threat": threat_summary.highest_threat.name,
                        "left_blind_spot": threat_summary.left_blind_spot_active,
                        "right_blind_spot": threat_summary.right_blind_spot_active,
                        "critical_collision": threat_summary.critical_collision_warning,
                        "min_ttc": threat_summary.minimum_ttc_seconds,
                        "speed_kmh": telemetry.speed_kmh if telemetry else 0.0,
                    })

    def start(self):
        server_instance = self

        class RequestHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                # Suppress noisy HTTP access logs in console
                pass

            def do_GET(self):
                if self.path in ("/", "/mirror"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(HTML_COCKPIT_TEMPLATE.encode("utf-8"))

                elif self.path == "/telemetry":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with server_instance._lock:
                        data = server_instance._latest_threat_json.encode("utf-8")
                    self.wfile.write(data)

                elif self.path == "/stream":
                    self.send_response(200)
                    self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={STREAM_BOUNDARY}")
                    self.send_header("Cache-Control", "no-cache, private")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()

                    try:
                        while True:
                            with server_instance._lock:
                                frame_data = server_instance._latest_jpeg

                            if frame_data:
                                self.wfile.write(f"--{STREAM_BOUNDARY}\r\n".encode("ascii"))
                                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                                self.wfile.write(f"Content-Length: {len(frame_data)}\r\n\r\n".encode("ascii"))
                                self.wfile.write(frame_data)
                                self.wfile.write(b"\r\n")
                            time.sleep(0.033)  # Cap at ~30 FPS per client
                    except (BrokenPipeError, ConnectionResetError):
                        pass

                else:
                    self.send_response(404)
                    self.end_headers()

        self._server = ThreadedHTTPServer((self.host, self.port), RequestHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"[✓] Indriyo Live Web Stream Server listening on http://{self.host}:{self.port}/mirror")

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
