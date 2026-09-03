Wiring motorcycle electronics requires extra care because bikes experience strong vibrations, weather exposure, and significant voltage spikes from the alternator.

Follow this complete wiring schematic and step-by-step assembly guide to wire the system safely and reliably.

---

### High-Level Circuit Architecture

```text
[ Motorcycle Battery / Switched 12V ]
       │
       ├───(+) Red Wire ──► [ 3A Inline Fuse ] ──► IN+ [ LM2596 Buck ] OUT+ ──┬──► (+) [1000µF Cap] ──► 5V  [ESP32-CAM Left]
       │                                                                      │
       │                                                                      └──► (+) [1000µF Cap] ──► 5V  [ESP32-CAM Right]
       │
       └───(-) Black Wire ───────────────────────► IN- [  Converter  ] OUT- ──┬──► (-) [1000µF Cap] ──► GND [ESP32-CAM Left]
                                                                              │
                                                                              └──► (-) [1000µF Cap] ──► GND [ESP32-CAM Right]

```

---

### Phase 1: Choosing Your 12V Source (Direct vs. Switched)

Do not leave the system running permanently on the battery:

* **Option A: Switched 12V Line (Recommended):** Tap into the **license plate light** or **tail running light** wire behind the tail plastics. This line automatically receives 12V only when the motorcycle key is turned to **ON**, meaning the system automatically turns off when you park, preventing parasitic battery drain.
* **Option B: Direct to Battery:** If you connect directly to the battery terminals, install a small toggle switch between the fuse and the buck converter so you can turn it off manually when parked.

---

### Phase 2: Wiring Step-by-Step

#### 1. Wire the 12V Input Side

1. Strip ~1 cm of insulation from your red positive wire.
2. Splice and solder the **3A Inline Fuse Holder** directly into the positive wire, keeping it as close to the 12V source as possible (within 10–15 cm).
3. Solder the other end of the fused red wire to the **`IN+`** pad of the LM2596 module.
4. Run a black ground wire from your negative terminal (or bike frame ground) directly to the **`IN-`** pad of the LM2596.

#### 2. The Golden Rule: Calibrate the Voltage FIRST

> **Warning:** Factory LM2596 modules often ship with the potentiometer adjusted to output 10V–12V. Connecting the ESP32s before calibrating will instantly burn their onboard voltage regulators.

1. Leave the ESP32-CAMs completely **disconnected**.
2. Turn your bike's ignition to **ON** to feed 12V to the LM2596. The power LED on the buck converter should light up.
3. Take a digital multimeter, set it to DC Voltage, and place the probes on **`OUT+`** and **`OUT-`**.
4. Use a small flathead screwdriver to turn the brass screw on the blue potentiometer **counter-clockwise** (it may require 5 to 10 full turns before the voltage begins dropping).
5. Adjust it until the multimeter reads **exactly 5.1V** (5.1V compensates for slight voltage drops over wire lengths under load).
6. Turn off the ignition.

#### 3. Wire the 5V Output Side (Parallel Setup)

Both ESP32-CAMs run in **parallel** so that each receives the full 5V supply:

1. Run two red wires from the LM2596 **`OUT+`** pad. Connect one to the **`5V`** pin of the Left ESP32-CAM, and the other to the **`5V`** pin of the Right ESP32-CAM.
2. Run two black wires from the LM2596 **`OUT-`** pad. Connect one to the **`GND`** pin of the Left ESP32-CAM, and the other to the **`GND`** pin of the Right ESP32-CAM.

#### 4. Solder the Anti-Brownout Capacitors

ESP32-CAMs experience sudden current spikes when activating Wi-Fi transmission. If voltage sags even for a fraction of a millisecond, the chip will trigger a brownout restart.

1. Take your **1000µF (or 470µF) electrolytic capacitors**.
2. Identify polarity: The long leg is **Positive (+)**, and the short leg next to the stripe on the casing is **Negative (-)**.
3. Solder one capacitor directly across the **5V and GND** wires as close to the physical ESP32 board as possible (ideally within 2 to 5 cm of the board).

---

### Phase 3: Motorcycle Ruggedization

* **Lock the Potentiometer:** Motorcycle engine vibration can cause the brass adjustment screw on the LM2596 to drift over time. Once you dial in 5.1V, add a drop of hot glue or clear nail polish on the screw head to lock it in place.
* **Insulate Every Joint:** Wrap every soldered connection in heat-shrink tubing. Electrical tape quickly unravels in the heat and rain.
* **Enclose the Electronics:** Place the LM2596 inside a small plastic project box tucked away under the pillion seat. Do not leave exposed circuit boards exposed to road spray or moisture.
