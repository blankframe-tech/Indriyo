#!/usr/bin/env python3
"""
Indriyo (ইন্দ্রিয়) - The Sixth Sense for Motorcyclists
Main CLI Execution and ADAS Dashboard Runner

Usage:
  python run_adas.py --simulate                 # Run realistic synthetic simulation
  python run_adas.py --stream http://192.168.4.1:81/stream  # Connect to ESP32-CAM
  python run_adas.py --webcam 0                 # Use local USB webcam
  python run_adas.py --benchmark                # Benchmark inference & TTC throughput
  python run_adas.py --headless                 # Run headless in terminal
"""

import argparse
import sys
import time
import cv2
import numpy as np

from indriyo_core.engine import IndriyoEngine
from indriyo_core.stream_receiver import MJPEGStreamReceiver, OpenCVStreamReceiver
from indriyo_core.synthetic_stream import SyntheticRearviewStream
from indriyo_core.telemetry import SimulatedTelemetry, SerialOBD2Telemetry
from indriyo_core.ttc_calculator import ThreatLevel


def print_banner():
    banner = r"""
===============================================================
  ___ _   _ ____  ____  _____   _____  
 |_ _| \ | |  _ \|  _ \|_ _\ \ / / _ \ 
  | ||  \| | | | | |_) || | \ V / | | |
  | || |\  | |_| |  _ < | |  | || |_| |
 |___|_| \_|____/|_| \_\___| |_| \___/ 
      ইন্দ্রিয় - The Sixth Sense for Motorcyclists
      Edge AI ADAS & Predictive Collision System
===============================================================
    """
    print(banner)


def run_benchmark(iterations: int = 100):
    print(f"\n[*] Starting Indriyo ADAS Benchmark ({iterations} iterations)...")
    synthetic = SyntheticRearviewStream(width=800, height=480, scenario="tailgater")
    telemetry = SimulatedTelemetry(base_speed_kmh=70.0)
    engine = IndriyoEngine(
        stream_receiver=synthetic,
        telemetry_source=telemetry,
        enable_audio=False
    )

    latencies = []
    t_start = time.time()

    for i in range(iterations):
        t0 = time.perf_counter()
        ret, frame, threat = engine.process_step()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
        if (i + 1) % 25 == 0:
            print(f"  Progress: {i+1}/{iterations} frames processed...")

    total_time = time.time() - t_start
    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    fps = iterations / total_time

    print("\n---------------- BENCHMARK RESULTS ----------------")
    print(f"Total Frames Processed: {iterations}")
    print(f"Total Time:             {total_time:.2f} s")
    print(f"Average Throughput:     {fps:.1f} FPS")
    print(f"Average Latency:        {avg_latency:.2f} ms")
    print(f"95th Percentile Latency:{p95_latency:.2f} ms")
    print(f"Real-Time Ready:        {'YES (Edge Capable)' if fps >= 25 else 'ADEQUATE'}")
    print("---------------------------------------------------\n")
    engine.close()


def main():
    parser = argparse.ArgumentParser(description="Indriyo ADAS Runner")
    parser.add_argument("--simulate", action="store_true", help="Run with synthetic simulated video")
    parser.add_argument("--scenario", choices=["tailgater", "blindspot", "dual_overtake", "dhaka_traffic"],
                        default="tailgater", help="Simulation scenario")
    parser.add_argument("--stream", type=str, help="URL of ESP32-CAM stream (e.g. http://192.168.4.1:81/stream)")
    parser.add_argument("--webcam", type=int, default=None, help="Webcam device index (0, 1)")
    parser.add_argument("--file", type=str, help="Video file path for testing")
    parser.add_argument("--obd-port", type=str, help="Serial port for ELM327 OBD-II adapter")
    parser.add_argument("--bike-speed", type=float, default=60.0, help="Simulated motorcycle cruising speed (km/h)")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmark")
    parser.add_argument("--headless", action="store_true", help="Run without OpenCV GUI window")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio alarm chimes")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (0 = continuous)")

    args = parser.parse_args()
    print_banner()

    if args.benchmark:
        run_benchmark()
        return

    # 1. Initialize Stream Receiver
    if args.stream:
        print(f"[*] Connecting to ESP32-CAM Stream: {args.stream}")
        stream = MJPEGStreamReceiver(args.stream)
    elif args.webcam is not None:
        print(f"[*] Initializing USB Webcam #{args.webcam}...")
        stream = OpenCVStreamReceiver(args.webcam)
    elif args.file:
        print(f"[*] Playing video file: {args.file}...")
        stream = OpenCVStreamReceiver(args.file)
    else:
        print(f"[*] Initializing Synthetic Rearview Simulation (Scenario: '{args.scenario}')...")
        stream = SyntheticRearviewStream(scenario=args.scenario)

    # 2. Initialize Telemetry
    if args.obd_port:
        print(f"[*] Initializing OBD-II Telemetry on {args.obd_port}...")
        telemetry = SerialOBD2Telemetry(port=args.obd_port)
    else:
        telemetry = SimulatedTelemetry(base_speed_kmh=args.bike_speed, mode="cruise")

    # 3. Initialize Engine
    engine = IndriyoEngine(
        stream_receiver=stream,
        telemetry_source=telemetry,
        enable_audio=not args.no_audio
    )

    print("\n[✓] Indriyo ADAS Engine Active.")
    print("    Press 'q' or Ctrl+C to terminate.")
    if not args.headless:
        print("    Press 's' to cycle simulation scenarios.")

    scenarios = ["tailgater", "blindspot", "dual_overtake", "dhaka_traffic"]
    curr_scenario_idx = 0
    frame_count = 0

    try:
        while True:
            ret, hud_frame, threat = engine.process_step()
            if not ret or hud_frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1
            if args.max_frames > 0 and frame_count >= args.max_frames:
                break

            if args.headless or cv2.__name__ == 'cv2' and not hasattr(cv2, 'imshow'):
                # Headless console logging
                status_icon = "🟢"
                if threat.highest_threat == ThreatLevel.CRITICAL:
                    status_icon = "🔴 CRITICAL!"
                elif threat.highest_threat == ThreatLevel.WARNING:
                    status_icon = "🟠 WARNING"
                
                if frame_count % 15 == 0:
                    print(f"[{time.strftime('%H:%M:%S')}] {status_icon} | Speed: {telemetry.get_telemetry().speed_kmh:.0f} km/h | "
                          f"FPS: {engine.fps:.1f} | Latency: {engine.latency_ms:.1f}ms | Threats: {threat.threat_count}")
                time.sleep(0.02)
            else:
                try:
                    cv2.imshow("Indriyo ADAS - Digital Rearview Mirror", hud_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('s') and isinstance(stream, SyntheticRearviewStream):
                        curr_scenario_idx = (curr_scenario_idx + 1) % len(scenarios)
                        next_sc = scenarios[curr_scenario_idx]
                        stream.set_scenario(next_sc)
                        print(f"[*] Switched to Scenario: {next_sc}")
                except Exception:
                    # In headless environments without display
                    pass

    except KeyboardInterrupt:
        print("\n[*] Stopping Indriyo ADAS...")
    finally:
        engine.close()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        print("[✓] Indriyo ADAS shutdown cleanly.")


if __name__ == "__main__":
    main()
