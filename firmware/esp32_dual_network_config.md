# Indriyo Dual-Camera Network Topologies

When running **two** ESP32-CAMs (one for the Left blind spot, one for the Right blind spot), there are two proven networking topologies.

---

## Topology 1: Single Bike Hotspot (Recommended - No Phone Hotspot Needed)

In this architecture, the **Left ESP32-CAM** creates a high-bandwidth local SoftAP network, and the **Right ESP32-CAM** connects to it as a Wi-Fi Station.

```text
       ┌──────────────────────────────┐
       │     Left ESP32-CAM           │
       │   (SoftAP: 192.168.4.1)      │
       └──────────────┬───────────────┘
                      │
           Wi-Fi Mesh / AP Connection
                      │
       ┌──────────────┴───────────────┐
       │     Right ESP32-CAM          │
       │   (Station: 192.168.4.2)     │
       └──────────────┬───────────────┘
                      │
               Rider's Phone
           (Indriyo App / ThrottleIQ)
           Ingests:
             - Left:  http://192.168.4.1:81/stream
             - Right: http://192.168.4.2:81/stream
```

### Setup Steps:
1. Flash **Left ESP32-CAM** with SoftAP enabled (`AP_SSID = "Indriyo_Network"`).
2. Flash **Right ESP32-CAM** with Station mode enabled:
   ```cpp
   #define CONNECT_TO_STATION
   #define STA_SSID     "Indriyo_Network"
   #define STA_PASSWORD "indriyo1234"
   ```
3. Connect your phone or Linux SBC to `Indriyo_Network`.
4. In the Indriyo Core or ThrottleIQ settings, enter:
   - Left Stream: `http://192.168.4.1:81/stream`
   - Right Stream: `http://192.168.4.2:81/stream`

---

## Topology 2: Phone Hotspot Gateway

If you prefer your smartphone to maintain cellular data (4G/5G) for GPS navigation (Google Maps / Waze) while running Indriyo:
1. Turn on **Personal Hotspot** on your smartphone (`SSID: "Indriyo_Host"`, `Password: "indriyo1234"`).
2. Flash both ESP32-CAMs in Station mode connecting to `"Indriyo_Host"`.
3. Check your phone's hotspot DHCP client table to get their assigned IPs (e.g., `172.20.10.2` and `172.20.10.3`).
4. Both streams run simultaneously without disrupting your phone's internet connection.
