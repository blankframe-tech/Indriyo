import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'indriyo_models.dart';
import 'mjpeg_stream_client.dart';

/// The Indriyo Digital Rearview Mirror HUD Widget for ThrottleIQ.
/// Displays live video from the motorcycle's tail camera with
/// peripheral warning borders (Amber / Flashing Red) and speed telemetry.
class IndriyoHudWidget extends StatefulWidget {
  final String streamUrl;
  final double currentSpeedKmh;
  final IndriyoThreatState threatState;
  final VoidCallback? onToggleFullscreen;

  const IndriyoHudWidget({
    Key? key,
    required this.streamUrl,
    required this.currentSpeedKmh,
    required this.threatState,
    this.onToggleFullscreen,
  }) : super(key: key);

  @override
  State<IndriyoHudWidget> createState() => _IndriyoHudWidgetState();
}

class _IndriyoHudWidgetState extends State<IndriyoHudWidget>
    with SingleTickerProviderStateMixin {
  late MjpegStreamClient _client;
  Uint8List? _latestFrame;
  late AnimationController _flashController;
  ThreatLevel _lastThreat = ThreatLevel.clear;

  @override
  void initState() {
    super.initState();
    _client = MjpegStreamClient(streamUrl: widget.streamUrl);
    _client.frameStream.listen((frame) {
      if (mounted) {
        setState(() {
          _latestFrame = frame;
        });
      }
    });
    _client.start();

    _flashController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 200),
    )..repeat(reverse: true);
  }

  @override
  void didUpdateWidget(covariant IndriyoHudWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.threatState.highestThreat != _lastThreat) {
      _lastThreat = widget.threatState.highestThreat;
      if (_lastThreat == ThreatLevel.critical) {
        HapticFeedback.heavyImpact();
      } else if (_lastThreat == ThreatLevel.warning) {
        HapticFeedback.mediumImpact();
      }
    }
  }

  @override
  void dispose() {
    _client.dispose();
    _flashController.dispose();
    super.dispose();
  }

  Color _getBorderColor() {
    if (widget.threatState.highestThreat == ThreatLevel.critical) {
      return _flashController.value > 0.5
          ? const Color(0xFFFF2A2A)
          : const Color(0x66FF2A2A);
    } else if (widget.threatState.highestThreat == ThreatLevel.warning) {
      return const Color(0xFFFF9500); // Amber
    } else {
      return const Color(0x3330D158); // Subtle Green
    }
  }

  @override
  Widget build(BuildContext context) {
    final borderColor = _getBorderColor();

    return AnimatedBuilder(
      animation: _flashController,
      builder: (context, child) {
        return Container(
          decoration: BoxDecoration(
            color: Colors.black,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: borderColor,
              width: widget.threatState.highestThreat == ThreatLevel.critical ? 6 : 3,
            ),
            boxShadow: [
              if (widget.threatState.highestThreat != ThreatLevel.clear)
                BoxShadow(
                  color: borderColor.withOpacity(0.4),
                  blurRadius: 18,
                  spreadRadius: 2,
                ),
            ],
          ),
          clipBehavior: Clip.antiAlias,
          child: Stack(
            fit: StackFit.expand,
            children: [
              // 1. Live Camera Stream
              if (_latestFrame != null)
                Image.memory(
                  _latestFrame!,
                  fit: BoxFit.cover,
                  gaplessPlayback: true,
                )
              else
                Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const CircularProgressIndicator(color: Color(0xFFFF9500)),
                      const SizedBox(height: 12),
                      Text(
                        'Connecting to Indriyo Tail Stream...',
                        style: TextStyle(
                          color: Colors.grey[400],
                          fontSize: 12,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                ),

              // 2. Blind Spot Side Indicators
              if (widget.threatState.leftBlindSpotActive)
                Align(
                  alignment: Alignment.centerLeft,
                  child: Container(
                    width: 14,
                    height: double.infinity,
                    color: const Color(0xFFFF9500),
                  ),
                ),
              if (widget.threatState.rightBlindSpotActive)
                Align(
                  alignment: Alignment.centerRight,
                  child: Container(
                    width: 14,
                    height: double.infinity,
                    color: const Color(0xFFFF9500),
                  ),
                ),

              // 3. Top Telemetry Banner
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Colors.black87, Colors.transparent],
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.radar, color: Color(0xFF00F0FF), size: 16),
                          const SizedBox(width: 6),
                          const Text(
                            'INDRIYO ADAS',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                              letterSpacing: 1.2,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        '${widget.currentSpeedKmh.toStringAsFixed(0)} KM/H',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                          fontSize: 16,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // 4. Critical Warning Center Strobe
              if (widget.threatState.criticalCollision && _flashController.value > 0.5)
                Center(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFF2A2A),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      '⚠️ COLLISION HAZARD - EVADE',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                        fontSize: 14,
                        letterSpacing: 1.5,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}
