# Indriyo

* **Indriyo (ইন্দ্রিয়)** meaning: Senses / organs of perception. Perfect.
* Writing up a well-structured MD document.

Structure:

# **Indriyo**

*The Sixth Sense for Motorcyclists*

## 1. Product Requirements Document (PRD)

* Target Audience
* Core Features
* Tech Arch (Hardware & Software)

## 2. Market Analysis: The White Space

* The current landscape (Tier 1 AI vs Tier 2 Radar vs Tier 3 Smart Dashboards)
* The Indriyo Competitive Advantage

## 3. POC Hardware Stack & Budget (Bangladesh - BDT)

Let's ensure it's beautifully formatted as Markdown and directly addresses everything.Here is the complete, updated PRD and Market Analysis unified into a single Markdown file, branded with your new name.

---

# **Indriyo (ইন্দ্রিয়)**

*The Sixth Sense for Motorcyclists*

**Product Vision:** To eliminate motorcycle blind spots and rear-end collisions by converting raw rear-facing video into an intelligent, predictive ADAS (Advanced Driver Assistance System) layer using edge AI.

*Indriyo* (Sanskrit/Bengali for "Sense" or "Organ of Perception") acts as an artificial nervous system for the motorcycle, giving the rider 360-degree situational awareness without requiring them to break their forward line of sight.

---

## Part 1: Product Requirements Document (PRD)

### 1. Target Audience

* **B2C:** Everyday commuters, touring riders, and sportbike enthusiasts who want premium aftermarket safety features without ruining the aesthetics of their motorcycles.
* **B2B:** Tier-1 motorcycle OEMs and smart-dashboard manufacturers looking to license turn-key AI middleware for next-gen digital clusters.

### 2. Core Features & User Experience

* **Active Blind Spot Detection (BSD):** Seamlessly identifies and tracks vehicles in the left and right rear zones.
* **Predictive Collision Warning (Time-to-Collision):** Differentiates between a vehicle pacing the motorcycle (safe) and a vehicle approaching at dangerous speeds (critical threat).
* **Intuitive "Peripheral" UI/UX:** A digital rearview mirror that uses color-coded perimeter lighting.
* *Warning State:* Solid amber border (Vehicle in blind spot).
* *Critical State:* Rapidly flashing red border (Rapidly approaching threat).
* *Goal:* The rider can process threats using peripheral vision without staring at the screen.


* **Adaptive Context:** Reads bike speed via OBD-II/CAN-bus to adjust threat sensitivity. (e.g., A car approaching at 40 km/h is a critical threat if the bike is stopped at a red light, but harmless if the bike is cruising at 80 km/h).

### 3. Technical Architecture

#### Hardware Stack

* **Processing Unit:** A single-board computer (SBC) capable of running TensorRT/ONNX optimized models at 30+ FPS (e.g., Raspberry Pi 5 or NVIDIA Jetson Nano/Orin series).
* **Cameras:** Dual ultra-wide-angle lenses (170°–180° FOV) with IP67 weather resistance and HDR to handle nighttime headlight glare. Mounted discreetly under the tail.
* **Display:** 4.3" or 5" IPS LCD bar screen (minimum 800+ nits for direct daylight visibility).
* **Vehicle Data Ingestion:** OBD-II (ELM327) or CAN-bus (MCP2515) interface.
* **Power:** 12V-to-5V step-down buck converter (minimum 3A to 5A output) wired to the motorcycle accessory line.

#### Software & ML Pipeline

1. **Ingestion:** Capture raw MIPI/CSI or USB camera streams.
2. **Detection (YOLO):** Run a lightweight object detection model (YOLOv8-Nano) to draw bounding boxes around vehicles. Filter out static infrastructure (trees, barriers) to prevent alert fatigue.
3. **Tracking & Vectoring:** Use Optical Flow or a tracking algorithm (like ByteTrack) to calculate the pixel expansion rate of bounding boxes (indicating approach speed).
4. **Logic Engine:** Compare approach speed with the motorcycle's current speed (via CAN-bus) to calculate Time-to-Collision (TTC).
5. **UI Rendering:** Overlay color-coded warning zones onto the video feed via an OpenCV or PyGame GUI.

---

## Part 2: Market Analysis & Competitive Landscape

The motorcycle ADAS market is currently highly fragmented. It is split between companies building **"dumb screens with cameras"** and companies building **"screen-less AI."** Indriyo sits directly in the highly profitable white space between these existing technologies.

### The Competition

**Tier 1: Direct AI Camera Competitors (Screenless)**

* *Players:* Ride Vision, Roadio, RiderDome.
* *How they work:* They use rear cameras and proprietary vision algorithms to track threats.
* *The Flaw:* They do **not** use a digital dashboard screen. They rely entirely on small LED indicator lights mounted to the stock physical mirrors. The rider gets an AI alert, but cannot actually see the threat without physically turning their head.

**Tier 2: Radar-Based ADAS (Automotive Grade)**

* *Players:* OEMs (Bosch), Aftermarket (Innovv ThirdEYE, Chigee SR-1, Garmin Varia).
* *How they work:* 24GHz or 77GHz radar modules mounted to the tail of the bike. They provide highly accurate distance and speed metrics.
* *The Flaw:* Radar cannot identify *what* an object is, only its mass. Furthermore, bulky radar boxes ruin the aesthetic lines of sportbikes, and radar systems provide no visual feed for the rider to verify the threat.

**Tier 3: Smart Dashboards (Visual Only)**

* *Players:* Chigee AIO-5 / AIO-6, Carpuride, AliExpress generics.
* *How they work:* Ultra-bright Apple CarPlay/Android Auto screens for motorcycles with front/rear dashcam recording.
* *The Flaw:* While newer premium models have basic Blind Spot Detection (BSD), they rely on rudimentary logic. They will warn a rider if a car is simply sitting in the blind spot, but struggle to calculate advanced **Time-to-Collision (TTC)** vectoring based on the bike's active speed.

### The Indriyo Competitive Advantage (The White Space)

1. **The "Trust but Verify" UI:** Ride Vision gives riders AI alerts without a screen. Smart dashes give riders screens without advanced AI. Indriyo gives them both: the AI grabs peripheral attention with a flashing border, and a millisecond later, the rider can look at the screen to visually verify the threat without turning their head.
2. **Context-Aware Logic:** Most aftermarket systems are "dumb" and flash constantly in heavy traffic because they only measure proximity, leading to alert fatigue. Indriyo scales its sensitivity based on the bike's actual speed via OBD-II/CAN-bus integration.
3. **Hardware Stealth:** Relying on dual stealthy lenses under the tail eliminates the bulky radar boxes or 360-degree dome cameras that riders refuse to mount on their machines.

---

## Part 3: POC Pricing Estimate (Dhaka, Bangladesh)

To build a working Proof of Concept (POC) in Bangladesh, custom PCBs are unnecessary. The prototype can be built using off-the-shelf development boards sourced from local electronics suppliers (e.g., TechshopBD, BDTronics, Daraz).

*Note: A Raspberry Pi 5 (8GB) is selected for the POC as it provides sufficient RAM and CPU power for edge inferencing. For production-grade AI, an NVIDIA Jetson Orin Nano is recommended, though it significantly increases the budget.*

| Component | Recommendation for BD Sourcing | Est. Price (BDT) |
| --- | --- | --- |
| **Brain / Processing Unit** | **Raspberry Pi 5 (8GB)** | ৳30,000 - ৳32,000 |
| **Cameras (Dual)** | 2x 1080p Wide-Angle USB Webcams or Pi Camera Modules (120-150° FOV) | ৳4,000 - ৳5,500 |
| **Dashboard Display** | **5-inch HDMI/DSI LCD** (Resistive or IPS, 800x480 resolution) | ৳4,500 - ৳5,000 |
| **Speed Sensor Data** | **ELM327 OBD-II Bluetooth/USB Scanner** or MCP2515 CAN Bus Module | ৳400 - ৳1,000 |
| **Power Management** | 12V to 5V 5A Step-down Buck Converter | ৳400 - ৳600 |
| **Casing & Mounting** | 3D Printed custom enclosures (Nilkhet/Elephant Road) & RAM mount clones | ৳2,000 - ৳3,000 |
| **Misc. Hardware** | High-speed MicroSD (64GB+), Cables, Active Cooler, WS2812B LED strips | ৳2,500 - ৳3,500 |
| **Total Est. POC Cost** | **Based on local Dhaka market rates** | **৳43,800 - ৳50,600** |
