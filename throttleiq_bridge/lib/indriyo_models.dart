import 'package:flutter/material.dart';

enum ThreatLevel {
  clear,
  monitoring,
  warning,  // Amber - vehicle in blind spot
  critical, // Flashing Red - collision imminent
}

enum ThreatZone {
  none,
  leftBlindSpot,
  rightBlindSpot,
  centerRear,
}

class IndriyoVehicleDetection {
  final String id;
  final String className;
  final Rect boundingBox;
  final double distanceMeters;
  final double relativeSpeedKmh;
  final double ttcSeconds;
  final ThreatLevel threatLevel;
  final ThreatZone zone;

  IndriyoVehicleDetection({
    required this.id,
    required this.className,
    required this.boundingBox,
    required this.distanceMeters,
    required this.relativeSpeedKmh,
    required this.ttcSeconds,
    required this.threatLevel,
    required this.zone,
  });
}

class IndriyoThreatState {
  final ThreatLevel highestThreat;
  final bool leftBlindSpotActive;
  final bool rightBlindSpotActive;
  final bool criticalCollision;
  final double minTtc;
  final List<IndriyoVehicleDetection> vehicles;
  final double fps;
  final double latencyMs;

  IndriyoThreatState({
    this.highestThreat = ThreatLevel.clear,
    this.leftBlindSpotActive = false,
    this.rightBlindSpotActive = false,
    this.criticalCollision = false,
    this.minTtc = -1.0,
    this.vehicles = const [],
    this.fps = 0.0,
    this.latencyMs = 0.0,
  });
}
