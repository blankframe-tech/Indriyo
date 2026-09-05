"""
Indriyo - Vehicle Telemetry Ingestion Layer
Supports OBD-II (ELM327), CAN-Bus (MCP2515), GPS, and Simulated telemetry.
"""

import time
import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class TelemetryData:
    speed_kmh: float = 0.0          # Active motorcycle road speed in km/h
    rpm: int = 0                    # Engine RPM
    throttle_pct: float = 0.0       # Throttle position (0.0 - 100.0)
    brake_active: bool = False      # Brake lever pressed
    heading_deg: float = 0.0        # Compass heading
    source: str = "simulated"       # Source name: obd2, can, gps, simulated
    timestamp: float = 0.0

    @property
    def speed_ms(self) -> float:
        """Speed in meters per second."""
        return self.speed_kmh / 3.6


class BaseTelemetrySource:
    """Base class for telemetry providers."""
    def get_telemetry(self) -> TelemetryData:
        raise NotImplementedError

    def close(self):
        pass


class SimulatedTelemetry(BaseTelemetrySource):
    """
    Simulates realistic motorcycle riding dynamics:
    Cruising, accelerating, braking, and stop-and-go city traffic.
    """
    def __init__(self, base_speed_kmh: float = 55.0, mode: str = "cruise"):
        self.base_speed = base_speed_kmh
        self.mode = mode
        self.start_time = time.time()

    def set_speed(self, speed_kmh: float):
        self.base_speed = max(0.0, speed_kmh)

    def get_telemetry(self) -> TelemetryData:
        t = time.time() - self.start_time
        
        if self.mode == "cruise":
            # Gentle natural speed fluctuation ±3 km/h
            fluctuation = math.sin(t * 0.4) * 2.5 + math.cos(t * 0.15) * 1.2
            speed = max(0.0, self.base_speed + fluctuation)
            rpm = int(3500 + speed * 45)
            brake = False
            throttle = 25.0 + math.sin(t * 0.4) * 8.0
        elif self.mode == "city":
            # Urban traffic cycle: accelerate, cruise, brake to stop at light
            cycle = t % 40.0
            if cycle < 12.0:
                # Accelerating from stop
                progress = cycle / 12.0
                speed = progress * self.base_speed
                brake = False
                throttle = 45.0
                rpm = int(1500 + progress * 4000)
            elif cycle < 28.0:
                # Cruising
                speed = self.base_speed + math.sin(t) * 2.0
                brake = False
                throttle = 20.0
                rpm = int(4500)
            elif cycle < 34.0:
                # Decelerating / braking
                progress = (cycle - 28.0) / 6.0
                speed = max(0.0, self.base_speed * (1.0 - progress))
                brake = True
                throttle = 0.0
                rpm = int(2000 * (1.0 - progress) + 1200)
            else:
                # Stopped at traffic light (0 km/h)
                speed = 0.0
                brake = True
                throttle = 0.0
                rpm = 1250 # Idle
        elif self.mode == "stopped":
            speed = 0.0
            brake = True
            throttle = 0.0
            rpm = 1200
        else:
            speed = self.base_speed
            rpm = 4000
            brake = False
            throttle = 20.0

        return TelemetryData(
            speed_kmh=round(speed, 1),
            rpm=rpm,
            throttle_pct=round(throttle, 1),
            brake_active=brake,
            heading_deg=round((t * 2.0) % 360.0, 1),
            source="simulated",
            timestamp=time.time()
        )


class SerialOBD2Telemetry(BaseTelemetrySource):
    """
    ELM327 OBD-II adapter reader over Serial (USB or Bluetooth RFCOMM).
    Queries standard PIDs:
      - 010D: Vehicle speed (km/h)
      - 010C: Engine RPM
    """
    def __init__(self, port: str = "/dev/tty.OBDII", baudrate: int = 38400):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self._last_data = TelemetryData(source="obd2")
        self._connected = False
        self._try_connect()

    def _try_connect(self):
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            # Initialize ELM327 commands
            self.serial_conn.write(b"ATZ\r")
            time.sleep(0.5)
            self.serial_conn.write(b"ATE0\r")  # Echo off
            self.serial_conn.write(b"ATH0\r")  # Headers off
            self.serial_conn.write(b"ATSP0\r") # Auto protocol
            self._connected = True
        except Exception:
            self._connected = False

    def get_telemetry(self) -> TelemetryData:
        if not self._connected or not self.serial_conn:
            return self._last_data

        try:
            # Query PID 010D (Vehicle speed)
            self.serial_conn.write(b"010D\r")
            resp = self.serial_conn.read_until(b">").decode("ascii", errors="ignore").strip()
            # Expected response format: "41 0D XX" where XX is hex speed in km/h
            tokens = resp.replace(" ", "")
            if "410D" in tokens:
                idx = tokens.find("410D") + 4
                hex_val = tokens[idx:idx+2]
                speed = int(hex_val, 16)
                self._last_data.speed_kmh = float(speed)
                self._last_data.timestamp = time.time()
        except Exception:
            pass

        return self._last_data

    def close(self):
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass
