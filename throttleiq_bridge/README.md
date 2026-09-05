# ThrottleIQ x Indriyo Integration Bridge

This folder provides drop-in Dart/Flutter components to bring real-time ADAS Blind Spot Detection and Time-to-Collision warnings into **ThrottleIQ**.

---

## 📦 What's Included

- `indriyo_models.dart`: Threat levels (`clear`, `monitoring`, `warning`, `critical`), spatial zones, and detection models.
- `mjpeg_stream_client.dart`: High-performance HTTP multipart MJPEG stream client with JPEG delimiter parsing.
- `indriyo_hud_widget.dart`: Animated digital rearview mirror HUD widget with peripheral Amber/Red warning borders and haptic feedback.

---

## 🛠️ How to Add to ThrottleIQ

1. Copy the `throttleiq_bridge/lib/` files into `ThrottleIQ/app/lib/features/indriyo/`.
2. Ensure your `pubspec.yaml` has:
   ```yaml
   dependencies:
     http: ^1.2.0
   ```
3. In your Ride Screen / Active Trip view, embed the `IndriyoHudWidget`:
   ```dart
   IndriyoHudWidget(
     streamUrl: 'http://192.168.4.1:81/stream',
     currentSpeedKmh: activeGpsSpeedKmh,
     threatState: currentThreatState,
   )
   ```
4. The widget automatically triggers device haptics (`HapticFeedback.heavyImpact()`) and flashes the red emergency border when a vehicle approaches rapidly from the rear!
