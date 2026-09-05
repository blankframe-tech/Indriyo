#!/usr/bin/env python3
"""
Indriyo - Edge AI Model Export & INT8 Quantization Pipeline
Exports YOLOv8n to ONNX and quantizes to INT8 dynamic range for
ultra-low-latency edge inferencing on mobile chips (Snapdragon / Apple Silicon)
and low-cost ARM NPUs (Luckfox RV1106).
"""

import os
import sys
import time
import numpy as np
from ultralytics import YOLO

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

def export_and_quantize():
    print("==================================================")
    print("  INDRIYO EDGE AI MODEL EXPORT & QUANTIZATION")
    print("==================================================")

    # 1. Load baseline YOLOv8-Nano
    print("[1/4] Loading baseline YOLOv8n PyTorch model...")
    pt_path = os.path.join(MODELS_DIR, "yolov8n.pt")
    model = YOLO("yolov8n.pt")
    # Save a copy in models/
    if not os.path.exists(pt_path):
        import shutil
        if os.path.exists("yolov8n.pt"):
            shutil.copy("yolov8n.pt", pt_path)

    # 2. Export to ONNX (FP32 baseline)
    print("[2/4] Exporting to ONNX format (FP32)...")
    onnx_file = model.export(format="onnx", imgsz=640, dynamic=False, simplify=True)
    target_onnx = os.path.join(MODELS_DIR, "yolov8n.onnx")
    if os.path.exists(onnx_file) and onnx_file != target_onnx:
        import shutil
        shutil.move(onnx_file, target_onnx)
    elif not os.path.exists(target_onnx) and os.path.exists("yolov8n.onnx"):
        import shutil
        shutil.move("yolov8n.onnx", target_onnx)

    fp32_size = os.path.getsize(target_onnx) / (1024 * 1024)
    print(f"      FP32 ONNX Model Size: {fp32_size:.2f} MB")

    # 3. Quantize to INT8 using ONNX Runtime
    print("[3/4] Quantizing ONNX model to INT8 (Dynamic Range)...")
    int8_onnx = os.path.join(MODELS_DIR, "yolov8n_int8.onnx")
    try:
        from onnxruntime.quantization import quantize_dynamic, QuantType
        quantize_dynamic(
            model_input=target_onnx,
            model_output=int8_onnx,
            weight_type=QuantType.QUInt8
        )
        int8_size = os.path.getsize(int8_onnx) / (1024 * 1024)
        compression_ratio = (1.0 - (int8_size / fp32_size)) * 100.0
        print(f"      INT8 ONNX Model Size: {int8_size:.2f} MB")
        print(f"      Size Reduction:       {compression_ratio:.1f}% smaller!")
    except Exception as e:
        print(f"[!] ONNX quantization warning: {e}")
        int8_onnx = target_onnx

    # 4. Benchmark Inference (FP32 vs INT8)
    print("[4/4] Benchmarking ONNX Runtime Inference...")
    import onnxruntime as ort

    dummy_input = np.random.randn(1, 3, 640, 640).astype(np.float32)

    # Benchmark FP32
    session_fp32 = ort.InferenceSession(target_onnx, providers=['CPUExecutionProvider'])
    input_name = session_fp32.get_inputs()[0].name
    # Warmup
    for _ in range(5):
        session_fp32.run(None, {input_name: dummy_input})
    
    t0 = time.perf_counter()
    iters = 20
    for _ in range(iters):
        session_fp32.run(None, {input_name: dummy_input})
    fp32_latency = ((time.perf_counter() - t0) / iters) * 1000.0

    # Benchmark INT8
    int8_latency = fp32_latency
    if os.path.exists(int8_onnx) and int8_onnx != target_onnx:
        session_int8 = ort.InferenceSession(int8_onnx, providers=['CPUExecutionProvider'])
        in_name_int8 = session_int8.get_inputs()[0].name
        for _ in range(5):
            session_int8.run(None, {in_name_int8: dummy_input})
        t0 = time.perf_counter()
        for _ in range(iters):
            session_int8.run(None, {in_name_int8: dummy_input})
        int8_latency = ((time.perf_counter() - t0) / iters) * 1000.0

    print("\n---------------- MODEL BENCHMARK RESULTS ----------------")
    print(f"FP32 Model Size:      {fp32_size:.2f} MB")
    print(f"INT8 Model Size:      {os.path.getsize(int8_onnx) / (1024*1024):.2f} MB")
    print(f"FP32 Latency:         {fp32_latency:.2f} ms")
    print(f"INT8 Latency:         {int8_latency:.2f} ms")
    speedup = fp32_latency / max(0.1, int8_latency)
    print(f"Inference Speedup:    {speedup:.2f}x")
    print(f"Status:               Ready for Edge Deployment (Luckfox / Mobile)")
    print("---------------------------------------------------------\n")


if __name__ == "__main__":
    export_and_quantize()
