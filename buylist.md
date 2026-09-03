Here is the exhaustive, down-to-the-wire Bill of Materials (BOM) to build the **Indriyo (Strategy 2) Proof of Concept** in Bangladesh.

This list includes everything you need to power the system directly from your motorcycle battery, protect it from power spikes, prevent the notorious ESP32 "brownout" restarts, and program it from your PC.

### 1. The Core AI Camera Pipeline

* **2x ESP32-CAM with OV2640 Camera Module**
* **Price:** ~৳800 – ৳950 each (Total: ~৳1,900)
* **Why:** These capture the video and host the local Wi-Fi MJPEG stream. Ensure it comes with the small camera ribbon attached.
* **Where to buy:** BDTronics, TechShopBD, or Daraz.


* **1x ESP32-CAM-MB (Micro USB Programmer Base)** *OR* **CP2102 USB to TTL Converter**
* **Price:** ~৳300 – ৳450
* **Why:** The ESP32-CAM does *not* have a USB port built-in for programming. You need this adapter to connect it to your computer once to upload the Arduino/ThrottleIQ code.
* *Pro-Tip:* Try to find the **"ESP32-CAM-MB"** shield on Daraz. It snaps directly onto the ESP32-CAM, meaning you don't have to mess with jumper wires to program it.



### 2. Power & Motorcycle Battery Integration

Motorcycle batteries run at 12V-14V (when the alternator is running), which will instantly fry a 5V ESP32. You must step the voltage down safely.

* **1x LM2596 DC-DC Step-Down Buck Converter (3A)**
* **Price:** ~৳150 – ৳260
* **Why:** Takes the 12V from the bike and drops it to a safe 5V for the ESP32s. You will turn the little gold screw on the blue box with a screwdriver until a multimeter reads exactly 5.0V on the output.


* **2x 1000µF (or 470µF) 16V Electrolytic Capacitors**
* **Price:** ~৳10 each (Total: ৳20)
* **Why:** **CRUCIAL.** ESP32-CAMs are notorious for pulling sudden power spikes when transmitting video over Wi-Fi, causing them to crash (known as a "Brownout Detector Reset"). Soldering one of these across the 5V and GND pins of each ESP32 acts as a power reserve and stabilizes the stream.


* **1x Inline ATC/ATO Fuse Holder + 3A or 5A Car Fuse**
* **Price:** ~৳80 – ৳150
* **Why:** Never wire electronics directly to a motorcycle battery without a fuse. If a wire pinches under your seat, this fuse blows and prevents a fire.



### 3. Wires, Soldering, & Connectivity

* **2 Meters of 22 AWG Hookup Wire (Red & Black)**
* **Price:** ~৳100
* **Why:** For the long run from the motorcycle battery (or accessory tail light wire) to the buck converter under the seat.


* **1x Strip of Dupont Jumper Wires (Female-to-Female & Male-to-Female)**
* **Price:** ~৳80
* **Why:** For bench-testing and connecting the ESP32 pins without soldering while you write the code.


* **Assorted Heat Shrink Tubing (2mm - 5mm)**
* **Price:** ~৳50 (for a small pack)
* **Why:** To wrap your soldered joints so they don't short out from motorcycle vibrations.


* **1x Micro USB Data Cable**
* **Price:** (You probably already have one)
* **Why:** To connect the programmer module to your PC. *Must* be a data-sync cable, not just a charging cable.



### 4. Enclosure & Mounting

* **1x Small Waterproof Plastic Junction Box / Project Box**
* **Price:** ~৳150 (Available at local electronics/hardware stores)
* **Why:** To house the LM2596 buck converter safely under the motorcycle seat, protected from rain.


* **Custom 3D Printed Housing (For the cameras)**
* **Price:** ~৳300 - ৳500
* **Why:** You will need to design or download a small dual-camera pod from Thingiverse and get it printed locally (e.g., at Nilkhet, Elephant Road, or via online 3D printing services in BD).



---

### 🛒 Where to Source in Bangladesh

You can buy 100% of these parts online with home delivery. Here are the top trusted robotic/electronics vendors in BD:

1. **TechShopBD** (techshopbd.com): Highly reliable, genuine parts, excellent customer service.
2. **BDTronics** (bdtronics.com): Great inventory for ESP32 and power modules.
3. **Robomart BD** (robomartbd.com): Good alternative for small components like capacitors and wires.
4. **Daraz BD:** Search "ESP32 CAM MB" on Daraz for complete kits shipped from overseas (usually takes 10-14 days but is very cheap).

### 💰 Total Estimated Cost

Your total hardware checkout cart should come out to roughly **৳2,600 to ৳3,200 BDT**.
