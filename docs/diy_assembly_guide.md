# Indriyo (ইন্দ্রিয়) DIY Hardware Assembly & Wiring Manual
**High-Performance Dual-Camera Motorcycle Rear ADAS Engine**
*Version 1.0 — Production-Grade Motorcycle Harness Installation Guide*

---

## Table of Contents
1. [Safety & Electrical Warnings](#1-safety--electrical-warnings)
2. [Complete Bill of Materials (BOM) & Tools](#2-complete-bill-of-materials-bom--tools)
3. [Full Circuit Schematic & Architecture](#3-full-circuit-schematic--architecture)
4. [Motorcycle Switched 12V Wire Color Matrix](#4-motorcycle-switched-12v-wire-color-matrix)
5. [Step-by-Step Bench Assembly & Calibration](#5-step-by-step-bench-assembly--calibration)
   - [Phase 1: Buck Converter Multimeter Calibration](#phase-1-buck-converter-multimeter-calibration)
   - [Phase 2: Anti-Brownout Capacitor Soldering](#phase-2-anti-brownout-capacitor-soldering)
   - [Phase 3: FTDI Firmware Flashing](#phase-3-ftdi-firmware-flashing)
6. [3D Printed Tail Pod & Lens Installation](#6-3d-printed-tail-pod--lens-installation)
7. [Motorcycle On-Board Installation & Cable Routing](#7-motorcycle-on-board-installation--cable-routing)
8. [Vibration Ruggedization & Waterproofing (IP65)](#8-vibration-ruggedization--waterproofing-ip65)
9. [Pre-Flight Verification Checklist & Troubleshooting](#9-pre-flight-verification-checklist--troubleshooting)

---

## 1. Safety & Electrical Warnings

> [!CAUTION]
> **ALWAYS DISCONNECT THE MOTORCYCLE BATTERY NEGATIVE TERMINAL** before touching any existing wiring loom. A direct short to the chassis frame can melt wiring or damage the motorcycle ECU.

> [!WARNING]
> **NEVER CONNECT THE ESP32-CAMs BEFORE CALIBRATING THE BUCK CONVERTER.**
> Factory LM2596 step-down modules are often shipped with the potentiometer dialed up to **10V–12V DC**. Connecting an ESP32 before tuning the trimpot to **5.1V** will instantly fry the onboard AMS1117 regulator and the ESP32 SoC.

> [!IMPORTANT]
> **USE ACID-FREE NEUTRAL CURE SILICONE ONLY.**
> Standard bathroom silicone cures using acetic acid (smells like vinegar), which corrodes copper PCB traces, SMD components, and solder joints within weeks. Use Dow Corning 737, MG Chemicals 422B Conformal Coating, or neutral cure electronics RTV.

---

## 2. Complete Bill of Materials (BOM) & Tools

### Core Electronics
| Component | Qty | Specification / Notes |
| :--- | :---: | :--- |
| **ESP32-CAM (AI-Thinker)** | 2 | OV2640 camera module, 160° Wide-Angle lens recommended |
| **LM2596 DC-DC Buck Converter** | 1 | 3A step-down, input 7–35V, output tuned to 5.1V |
| **Electrolytic Capacitors** | 2 | 1000 µF, 16V or 25V, Low-ESR (105°C rated) |
| **Ceramic Capacitors** (Optional) | 2 | 100 nF (0.1 µF) high-frequency decoupling |
| **Inline Mini Blade Fuse Holder** | 1 | Waterproof sealed cap, with **3A fast-blow fuse** |
| **FTDI USB-to-UART Adapter** | 1 | 3.3V logic level selectable, for initial flashing |

### Wiring & Mechanical Hardware
| Item | Qty | Specification |
| :--- | :---: | :--- |
| **Automotive Wire (AWG 18)** | 2m | Red (switched 12V) & Black (chassis ground) |
| **Stranded Hookup Wire (AWG 22)** | 2m | Red (+5V rail) & Black (GND rail) |
| **Dual-Wall Heat Shrink Tubing** | 1m | 3mm, 6mm, and 12mm with internal hot-melt adhesive |
| **Split-Loom Wire Conduit** | 1.5m | 6mm (1/4") corrugated automotive split tubing |
| **M3 Stainless Hex Bolts + Nyloc Nuts** | 4 | M3 x 12mm, A2 stainless steel |
| **Heavy-Duty UV-Resistant Zip Ties** | 20 | 150mm black nylon |
| **Posi-Tap Connectors** (or solder) | 2 | 16–18 AWG tap connectors for tapping tail light |

### Tools Required
- Digital Multimeter (measures DC volts to 2 decimal places)
- Temperature-controlled soldering iron with chisel/fine tip (lead-free or 60/40 rosin core solder)
- Wire strippers (AWG 18–24) and flush cutters
- Heat gun (or lighter for heat shrink)
- Small precision flathead screwdriver (for LM2596 potentiometer)

---

## 3. Full Circuit Schematic & Architecture

### Complete System Wiring Diagram
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MOTORCYCLE ELECTRICAL SYSTEM                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
      [Switched 12V Line]              │ [Chassis GND / Battery (-)]
      (e.g., Tail Light Wire)          │ (Black Wire)
               │                       │
               ▼                       ▼
      ┌─────────────────┐              │
      │ 3A Inline Fuse  │              │
      │  (Waterproof)   │              │
      └────────┬────────┘              │
               │ Red (18 AWG)          │ Black (18 AWG)
               ▼                       ▼
    ┌──────────────────────────────────────────────┐
    │          LM2596 DC-DC BUCK CONVERTER         │
    │  IN+                                     IN- │
    │                                              │
    │  [Trimpot: Calibrate to 5.10V DC]            │
    │                                              │
    │  OUT+                                   OUT- │
    └──────┬────────────────────────────────────┬──┘
           │ 5.1V Bus                           │ GND Bus
           │ (AWG 22 Red)                       │ (AWG 22 Black)
           ├─────────────────────────┬──────────┴──────────────┬──────────────────┐
           │                         │                         │                  │
           ▼                         ▼                         ▼                  ▼
    ┌──────────────┐          ┌──────────────┐          ┌──────────────┐   ┌──────────────┐
    │  1000 µF     │          │  LEFT POD    │          │  1000 µF     │   │  RIGHT POD   │
    │  Capacitor   │          │  ESP32-CAM   │          │  Capacitor   │   │  ESP32-CAM   │
    │  (+)     (-) │          │  5V      GND │          │  (+)     (-) │   │  5V      GND │
    └───┬───────┬──┘          └───┬───────┬──┘          └───┬───────┬──┘   └───┬───────┬──┘
        │       │                 │       │                 │       │          │       │
        └───────┼─────────────────┘       │                 └───────┼──────────┘       │
                └─────────────────────────┘                         └──────────────────┘
```

### Signal & Power Distribution Details
1. **12V Step-Down**: The LM2596 drops raw motorcycle alternator voltage (12.4V – 14.8V) down to a stable **5.10V DC**.
2. **5.10V Target Voltage**: Calibrating slightly above 5.00V overcomes resistance losses across 1–2 meters of wire and prevents the ESP32 internal 3.3V LDO from dropping below regulation during RF transmission peaks.
3. **Dual 1000µF Buffer Capacitors**: Positioned within **30 mm** of each ESP32 board. These act as localized energy reservoirs during 300mA 802.11 b/g/n transmission bursts.

---

## 4. Motorcycle Switched 12V Wire Color Matrix

Always tap into a **Switched 12V Accessory Line** (powered only when key is in **IGNITION ON**). This prevents the cameras from draining the battery while parked.

| Motorcycle Brand | Model Family | Switched 12V Wire (+) | Chassis Ground (-) | Recommended Tap Location |
| :--- | :--- | :--- | :--- | :--- |
| **Yamaha** | R15 (V3/V4), MT-15, FZ-S, R3 | **Blue / Red** or **Brown** | **Black** | License plate light sub-harness under pillion seat |
| **Honda** | CBR150R/250R, Hornet 2.0, CB350 | **Black** or **Red / Black** | **Green** | Tail lamp connector block under rear cowl |
| **Suzuki** | Gixxer 155/250, GSX-R150 | **Orange / White** or **Orange** | **Black / White** | Rear fender wiring harness |
| **Bajaj** | Pulsar N/F250, NS200, Dominar 400 | **Brown** or **White / Red** | **Black / Yellow** | Rear lighting loom behind tail tidy |
| **TVS** | Apache RTR 160/200 4V, RR 310 | **Orange** or **Red / Black** | **Black / White** | Under-seat auxiliary diagnostic or tail light block |
| **KTM** | Duke / RC 200/250/390 | **Orange** | **Brown** | ACC2 sub-harness behind rear tail plastic |
| **Royal Enfield** | Hunter 350, Meteor, Classic Reborn | **Orange / Green** | **Black** | Tail light connector behind side panel |

> [!TIP]
> **Verification with Multimeter**: Set multimeter to 20V DC. Touch the black probe to the battery negative terminal. Pierce or probe the candidate wire with the red probe.
> - Key **OFF**: Must read **0.00 V**.
> - Key **ON**: Must read **12.0 V – 12.8 V**.
> - Flip kill switch: Must remain **12.0 V** (so video does not drop if engine stalls).

---

## 5. Step-by-Step Bench Assembly & Calibration

### Phase 1: Buck Converter Multimeter Calibration

```text
[Bench 12V / Battery] ──► [IN+  LM2596  IN-]
                                  │
                           [Screw Trimpot] ◄── [Turn Counter-Clockwise 8–15 turns]
                                  │
                          [OUT+         OUT-]
                            │             │
                            ▼             ▼
                      [ Multimeter: 5.10 V DC ]
```

1. Secure the LM2596 module in a helping hand or PCB clamp.
2. Solder temporary input wires to `IN+` and `IN-`. Connect to a 12V power supply or motorcycle battery.
3. Turn on the 12V supply. The onboard LED will illuminate.
4. Set your digital multimeter to **DC Volts (20V range)**.
5. Place the red test lead on `OUT+` and the black test lead on `OUT-`.
6. Look at the brass potentiometer screw on the blue box. **Using a precision flathead screwdriver, turn it counter-clockwise 8 to 15 full revolutions** until you see the voltage drop below 6.0V.
7. Fine-tune until the display reads **5.10V to 5.15V DC**.
8. **Vibration Lock**: Dab a tiny droplet of clear nail polish, hot glue, or threadlocker onto the brass screw to prevent vibration drift.

---

### Phase 2: Anti-Brownout Capacitor Soldering

```text
        ESP32-CAM Top View
       ┌──────────────────┐
       │   [OV2640 Lens]  │
       │                  │
       │ 5V          GND  │
       └──┬────────────┬──┘
          │            │
          │            │
         (+)          (-)  ◄── 1000 µF 16V Low-ESR Capacitor
      ┌───┴────────────┴───┐
      │  [==== 1000µF ===] │
      │   Long     Stripe  │
      │   Lead     (Short) │
      └────────────────────┘
```

1. **Identify Capacitor Polarity**:
   - **Positive (+) Lead**: Longer wire leg.
   - **Negative (-) Lead**: Shorter wire leg, marked with a thick white or gold stripe with **minus (`-`) signs** on the capacitor body.
2. Cut the capacitor legs down to ~15 mm.
3. Strip 3 mm off your AWG 22 power wires.
4. Slip a piece of 3 mm heat shrink over each wire.
5. Solder the **Positive lead** of the capacitor directly together with the `+5V` wire entering the ESP32-CAM `5V` pin.
6. Solder the **Negative lead** of the capacitor directly together with the `GND` wire entering the ESP32-CAM `GND` pin.
7. Slide heat shrink over each lead and shrink with hot air.

---

### Phase 3: FTDI Firmware Flashing

```text
  FTDI Adapter (Set to 3.3V)          ESP32-CAM (AI-Thinker)
  ┌────────────────────────┐          ┌──────────────────────┐
  │ VCC (5V Out) ──────────┼──────────┤ 5V                   │
  │ GND ───────────────────┼──────────┤ GND                  │
  │ TX ────────────────────┼──────────┤ U0R (RX)             │
  │ RX ────────────────────┼──────────┤ U0T (TX)             │
  └────────────────────────┘          │                      │
                                      │ GPIO 0 ──┐           │
                                      │          │ (Jumper)  │
                                      │ GND    ──┘           │
                                      └──────────────────────┘
```

1. Connect **GPIO 0 to GND** on the ESP32-CAM using a female jumper wire. This puts the ESP32 in UART bootloader flashing mode.
2. Plug the FTDI adapter into your workstation USB port.
3. Flash the Left Camera firmware:
   ```bash
   cd firmware/esp32_cam
   # Flash Left Camera
   pio run -e left_cam --target upload
   ```
4. Flash the Right Camera firmware:
   ```bash
   # Flash Right Camera
   pio run -e right_cam --target upload
   ```
5. **Disconnect GPIO 0 from GND** and press the small `RST` tactile switch on the bottom of the ESP32.
6. Open serial monitor at 115200 baud to verify Wi-Fi connection and MJPEG stream URL:
   ```text
   WiFi connected: Indriyo_AP
   Camera Ready! Stream at: http://192.168.4.10:81/stream
   ```

---

## 6. 3D Printed Tail Pod & Lens Installation

```text
 ┌─────────────────────────────────────────────────────────────────┐
 │               DUAL-CAMERA REAR TAIL POD (TOP VIEW)              │
 │                                                                 │
 │         15° Outward                                15° Outward  │
 │            Left                                      Right      │
 │          ┌──────┐                                   ┌──────┐    │
 │          │ LENS │                                   │ LENS │    │
 │       ┌──┴──────┴──┐                             ┌──┴──────┴──┐ │
 │       │ ESP32-CAM  │                             │ ESP32-CAM  │ │
 │       │    (L)     │                             │    (R)     │ │
 │       └────────────┘                             └────────────┘ │
 │             \                                           /       │
 │              \   ◄── Central Gland Cable Exit ──►      /        │
 │               \                                       /         │
 └─────────────────────────────────────────────────────────────────┘
```

1. **Print Settings**:
   - Material: **PETG or ABS/ASA** (do NOT use standard PLA; it deforms in sunlight and engine heat above 55°C).
   - Infill: **40% Gyroid**.
   - Wall Perimeters: **4 walls** (1.6mm) for structural rigidity against road bumps.
2. Insert each OV2640 camera ribbon through the lens bezel slot.
3. Slide each ESP32-CAM board into the guide rails until fully seated.
4. Align the 15° outward splay:
   - **Left Camera**: Angles 15° left to cover the left rear quarter and blind spot.
   - **Right Camera**: Angles 15° right to cover the right rear quarter and overtaking vehicles.
   - Center overlap: 40° field of view overlap in the direct rear for distance triangulation.
5. Secure the pod back cover using four **M3 x 12mm stainless hex screws**.

---

## 7. Motorcycle On-Board Installation & Cable Routing

```text
                  MOTORCYCLE CHASSIS SIDE PROFILE
                  
  [Handlebars]                                       [Tail Pod]
   Display HUD ──┐                                   ┌── Dual Cameras
                 │                                   │
                 ▼                                   ▼
          ┌─────────────┐   Under Tank / Seat  ┌─────────────┐
          │ Phone / Nav │══════════════════════│ Tail Light  │
          │ Display     │   Split Loom Tube    │ Sub-Harness │
          └─────────────┘                      └──────┬──────┘
                                                      │
                                                      ▼
                                               [LM2596 Under
                                                Pillion Seat]
```

### Installation Steps
1. **Mount the Tail Pod**:
   - Mount under or directly above the rear license plate bracket using two M5 or M6 stainless bolts with Nyloc locking nuts and rubber anti-vibration washers.
   - Ensure horizontal alignment with the motorcycle axle.
2. **Mount the LM2596 Enclosure**:
   - Tuck the buck converter project box inside the under-seat storage tray / tool tray where it is shielded from direct water spray.
   - Secure with 3M Dual Lock or heavy-duty outdoor VHB tape.
3. **Route the Wiring**:
   - Run the 18 AWG power pair forward from the tail light tap into the buck converter `IN`.
   - Run the 22 AWG power pair from the buck converter `OUT` to the tail pod inside **6mm corrugated automotive split-loom tubing**.
   - Secure the conduit to the motorcycle subframe using UV-stabilized zip ties every 15–20 cm.
   - **CRITICAL**: Maintain at least **10 cm clearance from exhaust headers and rear shock linkage**. Never run wires where they can be pinched by full rear suspension travel.

---

## 8. Vibration Ruggedization & Waterproofing (IP65)

Motorcycles subject electronics to continuous multi-axis vibration (10–1000 Hz) and harsh weather (monsoon rain, road salt, pressure washing). Follow these protection protocols:

1. **PCB Conformal Coating**:
   - Mask the camera sensor lens opening and the Wi-Fi antenna trace with Kapton tape.
   - Spray or brush two coats of **MG Chemicals 422B Silicone Conformal Coating** over the entire front and back of the ESP32-CAM board.
   - Allow 30 minutes to cure before assembly.
2. **Lens Sealing**:
   - Apply a continuous bead of **neutral-cure silicone sealant (Dow Corning 737)** around the perimeter of the camera lens aperture on the outside face of the 3D pod.
3. **Cable Entry Gland**:
   - Ensure the cable entry hole at the rear of the pod faces **downwards or backwards**.
   - Fill the cable gland entry with neutral silicone RTV or install a rubber IP67 cable grommet to prevent capillary water ingress along the wire bundle.
4. **Drip Loop**:
   - Leave a 3 cm drooping "drip loop" in the wire harness just before entering the pod so water runs off by gravity rather than following the wire into the enclosure.

---

## 9. Pre-Flight Verification Checklist & Troubleshooting

### Bench Checklist
- [ ] Multimeter verifies buck converter output is **5.10V ± 0.05V**.
- [ ] Trimpot locked with threadlocker / nail polish.
- [ ] 1000µF capacitors installed with correct polarity.
- [ ] ESP32 boards boot clean without continuous brownout resets.
- [ ] Left camera stream accessible at `http://192.168.4.10:81/stream`.
- [ ] Right camera stream accessible at `http://192.168.4.11:81/stream`.

### On-Bike Checklist
- [ ] Inline 3A fuse installed within 15 cm of switched 12V tap.
- [ ] System powers on only with ignition key set to ON.
- [ ] System cuts power when ignition key set to OFF.
- [ ] Full rear suspension bounce test verifies wires cannot snag on swingarm or tire.
- [ ] Real-time ADAS engine connects:
  ```bash
  python run_adas.py --left http://192.168.4.10:81/stream --right http://192.168.4.11:81/stream --serve
  ```
- [ ] Threat alerts (TTC < 1.8s) audible through helmet Bluetooth intercom or visible on ThrottleIQ HUD.

### Troubleshooting Quick Reference
| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **ESP32 loops in "Brownout detector was triggered"** | Voltage sag during Wi-Fi transmission peak (>300mA) | Increase capacitor to 1000µF Low-ESR; increase buck voltage from 5.0V to 5.15V. |
| **Camera image pink or purple tint** | OV2640 ribbon cable not seated properly | Unlock ribbon clamp, re-seat ribbon perfectly perpendicular, close clamp. |
| **No power to LM2596 LED** | Blown fuse or tapped into wrong wire | Check 3A fuse continuity with multimeter; check ground wire connection. |
| **Wi-Fi signal drops while riding** | Metal tail frame shielding onboard PCB antenna | Solder external 2.4GHz IPEX antenna or route ESP32 antenna away from steel subframe. |
