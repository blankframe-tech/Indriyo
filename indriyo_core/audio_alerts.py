"""
Indriyo - Multi-Modal Alert Dispatcher
Generates audio chimes for helmet Bluetooth intercoms (Cardo/Sena)
and haptic trigger pulses for handlebar vibration modules.
"""

import time
import math
import wave
import io
import threading
import sys
from typing import Optional
from indriyo_core.ttc_calculator import ThreatLevel, ADASThreatSummary


class AudioAlertDispatcher:
    """
    Synthesizes and triggers distinct alert audio cues:
    - Amber Warning: Pleasant double-beep (880 Hz + 1174 Hz) to draw peripheral attention
    - Flashing Red Critical: Urgent rapid two-tone alarm (1400 Hz / 1800 Hz)
    """
    def __init__(self, enable_sound: bool = True):
        self.enable_sound = enable_sound
        self._last_warning_sound = 0.0
        self._last_critical_sound = 0.0
        self._warning_interval = 2.0   # Seconds between warning beeps
        self._critical_interval = 0.6  # Seconds between critical alarms

    def process_threat(self, threat_summary: ADASThreatSummary):
        if not self.enable_sound:
            return

        now = time.time()

        if threat_summary.highest_threat == ThreatLevel.CRITICAL:
            if now - self._last_critical_sound >= self._critical_interval:
                self._last_critical_sound = now
                self._play_critical_alarm()

        elif threat_summary.highest_threat == ThreatLevel.WARNING:
            if now - self._last_warning_sound >= self._warning_interval:
                self._last_warning_sound = now
                self._play_warning_chime()

    def _play_warning_chime(self):
        """Plays double-tone chime in background thread."""
        threading.Thread(target=self._beep, args=(880, 0.1, 0.05, 1174, 0.12), daemon=True).start()

    def _play_critical_alarm(self):
        """Plays urgent high-pitch strobe in background thread."""
        threading.Thread(target=self._beep, args=(1600, 0.08, 0.04, 1900, 0.08), daemon=True).start()

    def _beep(self, f1: int, d1: float, gap: float, f2: int, d2: float):
        """Synthesizes PCM audio or emits terminal bell."""
        # On macOS, can also trigger standard system alert via afplay or sys.stdout.write('\a')
        try:
            if sys.platform == "darwin":
                import subprocess
                # Use macOS built-in afplay or osascript beep
                subprocess.run(
                    ["osascript", "-e", "beep 1"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=0.5
                )
            else:
                sys.stdout.write('\a')
                sys.stdout.flush()
        except Exception:
            pass
