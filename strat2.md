This is a brilliant pivot. Integrating **Indriyo** as a real-time feature directly into **ThrottleIQ** is the perfect way to bridge your existing ecosystem.

Right now, ThrottleIQ is handling macro-level safety (crash data analysis, heatmaps, and analytics). By adding Indriyo, you instantly transform ThrottleIQ from a *retrospective* safety app into an **active, real-time driver-assist dashboard**.

Here is how we execute **Strategy 2 (The Smartphone Brain)** and integrate it seamlessly into ThrottleIQ.

---

# **Indriyo x ThrottleIQ**

*Real-Time ADAS Integration Architecture*

### 1. The Synergy (Why this works)

Instead of forcing the rider to mount an expensive secondary screen, they just mount their phone on the handlebars (which they are likely doing anyway for GPS).

* **The Bike's Role:** Acts as a "dumb" wireless camera pipeline.
* **ThrottleIQ's Role:** Acts as the "smart" brain. It ingests the video, runs the YOLOv8 model locally on the mobile processor (via TensorFlow Lite or CoreML), calculates Time-to-Collision (TTC), and displays the digital mirror UI.

### 2. The Technical Workflow

Here is how the data flows from the back of the motorcycle to the ThrottleIQ app:

#### Step A: Hardware Capture (The ESP32-CAMs)

1. Two **ESP32-CAM** modules (Left and Right) are mounted under the tail section.
2. One of the ESP32s is set as an Access Point (Wi-Fi Hotspot) named `Indriyo_Network`.
3. The modules continuously capture video at a lower, stable resolution (e.g., QVGA 320x240 or VGA 640x480) to maintain a high frame rate and low latency over Wi-Fi.
4. The video is compressed into an **MJPEG stream** and hosted on a lightweight local web server via the ESP32s.

#### Step B: The ThrottleIQ App Bridge

1. The rider mounts their phone and connects their Wi-Fi to `Indriyo_Network`.
2. They open **ThrottleIQ** and tap a new "Ride Mode" or "Indriyo Dash" button.
3. The app connects to the ESP32 IP addresses (e.g., `192.168.4.1:81/stream`) and starts pulling the live MJPEG frames.

#### Step C: Mobile Edge-AI (The Heavy Lifting)

1. **Inferencing:** ThrottleIQ passes the incoming frames through a lightweight, mobile-optimized object detection model (like **YOLOv8n-int8** or **MobileNetV2** converted to `.tflite` for Android or `.mlmodel` for iOS).
2. **Tracking:** The app calculates the bounding box expansion rate (Optical Flow/TTC).
3. **Speed Data:** Since you are using a phone, ThrottleIQ can use the smartphone's built-in **GPS** to determine the motorcycle's speed in real-time, completely eliminating the need for complex OBD-II or CAN-bus hardware on the bike!

#### Step D: The Dashboard UI

1. ThrottleIQ splits the screen: perhaps a live map/nav on top, and the Indriyo rear-camera feeds on the bottom.
2. If a vehicle approaches too fast, ThrottleIQ flashes the borders of the phone screen (Amber/Red) and can even trigger the phone's **haptic motor** (vibration) or play an audible ping through the rider's Bluetooth helmet comms (Cardo/Sena).

---

### 3. Revised Bangladesh BOM (The Under-৳3,000 Setup)

Because the smartphone does the heavy lifting, your hardware cost drops to almost nothing. You can prototype this in Dhaka this weekend.

| Component | Purpose | Est. Price (BDT) |
| --- | --- | --- |
| **2x ESP32-CAM Modules** (with OV2640 camera sensors) | Video capture & Wi-Fi streaming | ৳1,200 - ৳1,400 (Total) |
| **1x FTDI Programmer (CP2102)** | Needed once to upload the code from your PC to the ESP32-CAMs | ৳250 - ৳300 |
| **12V to 5V Step-Down Buck Converter (3A)** | Drops motorcycle battery voltage to safe 5V USB power | ৳300 - ৳400 |
| **Custom 3D Printed Housing** | To weatherproof the ESP32-CAMs under the tail | ৳500 - ৳800 |
| **Misc (Wires, capacitors)** | Prototyping essentials | ৳200 |
| **Total Est. POC Cost** |  | **৳2,450 - ৳3,100** |

### 4. Next Steps for Development

1. **Hardware Test:** Buy a single ESP32-CAM and an FTDI programmer. Flash it with the standard `CameraWebServer` sketch (available in the Arduino IDE examples). See if you can stream the video to your phone's browser smoothly.
2. **App Test:** Update the ThrottleIQ codebase (React Native/Flutter/Swift) to ingest an MJPEG stream from an IP address.
3. **AI Test:** Integrate TensorFlow Lite into ThrottleIQ. Test if the phone can run bounding boxes over the live MJPEG stream without dropping too many frames or overheating the phone.
