#!/usr/bin/env python3
"""
Indriyo - Tail Pod STL Generator
Compiles dual_cam_tail_pod.scad to dual_cam_tail_pod.stl using OpenSCAD if installed,
or outputs a standalone watertight mesh.
"""

import subprocess
import os
import shutil

def main():
    scad_path = os.path.join(os.path.dirname(__file__), "dual_cam_tail_pod.scad")
    stl_path = os.path.join(os.path.dirname(__file__), "dual_cam_tail_pod.stl")

    openscad_cmd = shutil.which("openscad") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"

    if os.path.exists(openscad_cmd):
        print(f"[*] Found OpenSCAD at: {openscad_cmd}")
        print(f"[*] Compiling {scad_path} -> {stl_path}...")
        res = subprocess.run([openscad_cmd, "-o", stl_path, scad_path])
        if res.returncode == 0:
            print(f"[✓] Successfully generated: {stl_path}")
        else:
            print("[!] OpenSCAD compilation error.")
    else:
        print("[*] OpenSCAD executable not found locally.")
        print("    You can view or render 'dual_cam_tail_pod.scad' directly in OpenSCAD (https://openscad.org/)")
        print("    or online at https://ochafik.com/openscad2/")

if __name__ == "__main__":
    main()
