# Indriyo (ইন্দ্রিয়) ESP32-CAM Firmware Guide

This firmware turns standard **AI-Thinker ESP32-CAM** modules (~৳800–৳950 in Bangladesh) into dedicated, ultra-low-latency wireless video streams for motorcycle Blind Spot Detection (BSD).

---

## 🚀 Quick Setup & Flashing

### Option A: Using Arduino IDE
1. Install **ESP32 Board Support** in Arduino IDE (`File > Preferences > Additional Boards Manager URLs`):
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
2. Select Board: **"AI Thinker ESP32-CAM"**.
3. Set CPU Frequency: **240MHz (WiFi/BT)**.
4. Set Flash Frequency: **80MHz**.
5. Set Flash Mode: **QIO**.
6. Set Partition Scheme: **Huge APP (3MB No OTA / 1MB SPIFFS)**.
7. Connect your **ESP32-CAM-MB** programmer shield via Micro USB (or use an FTDI adapter with `GPIO 0` connected to `GND`).
8. Press **Upload**. Once uploaded, remove the `GPIO 0` jumper wire (if using FTDI) and press the RST button.

### Option B: Using PlatformIO
```bash
cd firmware/esp32_cam_streamer
pio run -t upload
pio device monitor -b 115200
```

---

## ⚙️ Camera Role Configuration (Left vs Right)

Open `esp32_cam_streamer.ino` and edit lines 34-49:

- **For Left Tail Camera:**
  ```cpp
  #define IS_LEFT_CAMERA 1
  ```
  Creates SoftAP SSID: `Indriyo_Left_Cam` (Default IP: `192.168.4.1`)
  Stream URL: `http://192.168.4.1:81/stream`

- **For Right Tail Camera:**
  ```cpp
  #define IS_LEFT_CAMERA 0
  ```
  Creates SoftAP SSID: `Indriyo_Right_Cam` (Default IP: `192.168.4.1`)
  Stream URL: `http://192.168.4.1:81/stream`

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `http://192.168.4.1:81/stream` | GET | Continuous low-latency multipart/x-mixed-replace MJPEG stream (30 FPS) |
| `http://192.168.4.1/capture` | GET | Single JPEG snapshot |
| `http://192.168.4.1/status` | GET | JSON diagnostics (Free heap, resolution, active clients, frame count) |
| `http://192.168.4.1/control?var=X&val=Y` | GET | Adjust brightness, contrast, flip, framesize on the fly |

---

## ⚡ Hardware Tips for Motorcycle Installation
1. **Always solder a 1000µF 16V electrolytic capacitor** directly across `5V` and `GND` within 3cm of the ESP32-CAM pins.
2. **Never feed raw 12V** to the board. Use the LM2596 buck converter adjusted to exactly `5.1V`.
3. **Lock the LM2596 potentiometer screw** with a drop of glue or nail polish to prevent vibration drift.
