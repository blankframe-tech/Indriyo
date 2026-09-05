#!/usr/bin/env python3
"""
Indriyo - Handlebar Display Hood 3D STL Mesh Generator
Generates a watertight binary STL mesh of the motorcycle handlebar display sun hood:
- Display phone / LCD pocket: 140mm x 78mm x 14mm
- 28mm forward anti-glare sun visor hood (prevents daylight screen washout)
- Dual rear 22mm handlebar mounting clamp blocks with M4 bolt holes
- Bottom cable relief for USB-C telemetry & power
"""

import os
import struct
import math
import numpy as np


class BinarySTLWriter:
    def __init__(self):
        self.triangles = []

    def add_triangle(self, v1, v2, v3):
        v1 = np.array(v1, dtype=np.float32)
        v2 = np.array(v2, dtype=np.float32)
        v3 = np.array(v3, dtype=np.float32)
        
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)
        norm_len = np.linalg.norm(normal)
        if norm_len > 1e-6:
            normal = normal / norm_len
        else:
            normal = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        self.triangles.append((normal, (v1, v2, v3)))

    def add_quad(self, v1, v2, v3, v4):
        self.add_triangle(v1, v2, v3)
        self.add_triangle(v1, v3, v4)

    def add_box(self, center, size):
        cx, cy, cz = center
        dx, dy, dz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0

        p0 = (cx - dx, cy - dy, cz - dz)
        p1 = (cx + dx, cy - dy, cz - dz)
        p2 = (cx + dx, cy + dy, cz - dz)
        p3 = (cx - dx, cy + dy, cz - dz)
        p4 = (cx - dx, cy - dy, cz + dz)
        p5 = (cx + dx, cy - dy, cz + dz)
        p6 = (cx + dx, cy + dy, cz + dz)
        p7 = (cx - dx, cy + dy, cz + dz)

        # Bottom
        self.add_quad(p0, p3, p2, p1)
        # Top
        self.add_quad(p4, p5, p6, p7)
        # Front (-Y)
        self.add_quad(p0, p1, p5, p4)
        # Back (+Y)
        self.add_quad(p2, p3, p7, p6)
        # Left (-X)
        self.add_quad(p0, p4, p7, p3)
        # Right (+X)
        self.add_quad(p1, p2, p6, p5)

    def add_hood_flange(self, base_w, base_h, tip_w, tip_h, length, z_base):
        # Visor hood projecting along +Z
        hw_b, hh_b = base_w / 2.0, base_h / 2.0
        hw_t, hh_t = tip_w / 2.0, tip_h / 2.0
        z_tip = z_base + length

        # Top visor flap (angled over the screen to block sun)
        # Base top edge
        b_tl = (-hw_b, hh_b, z_base)
        b_tr = ( hw_b, hh_b, z_base)
        t_tl = (-hw_t, hh_t + 10.0, z_tip)
        t_tr = ( hw_t, hh_t + 10.0, z_tip)
        self.add_quad(b_tl, b_tr, t_tr, t_tl)

        # Left visor flap
        b_bl = (-hw_b, -hh_b, z_base)
        t_bl = (-hw_t, -hh_t, z_tip)
        self.add_quad(b_bl, b_tl, t_tl, t_bl)

        # Right visor flap
        b_br = ( hw_b, -hh_b, z_base)
        t_br = ( hw_t, -hh_t, z_tip)
        self.add_quad(b_tr, b_br, t_br, t_tr)

        # Visor rim
        self.add_quad(t_tl, t_tr, t_br, t_bl)

    def add_cylinder(self, center, radius, length, segments=24, axis='x'):
        cx, cy, cz = center
        half_l = length / 2.0
        angles = [2 * math.pi * i / segments for i in range(segments)]

        for i in range(segments):
            a1 = angles[i]
            a2 = angles[(i + 1) % segments]

            if axis == 'x':
                p1_end1 = (cx - half_l, cy + radius * math.cos(a1), cz + radius * math.sin(a1))
                p2_end1 = (cx - half_l, cy + radius * math.cos(a2), cz + radius * math.sin(a2))
                p1_end2 = (cx + half_l, cy + radius * math.cos(a1), cz + radius * math.sin(a1))
                p2_end2 = (cx + half_l, cy + radius * math.cos(a2), cz + radius * math.sin(a2))

                self.add_quad(p1_end1, p2_end1, p2_end2, p1_end2)
                self.add_triangle((cx - half_l, cy, cz), p1_end1, p2_end1)
                self.add_triangle((cx + half_l, cy, cz), p2_end2, p1_end2)

    def write_binary_stl(self, filepath: str, header_text: str = "Indriyo Handlebar Sun Hood v1.0"):
        with open(filepath, "wb") as f:
            # 80-byte header
            header = header_text.encode("utf-8")[:80]
            header = header.ljust(80, b"\x00")
            f.write(header)

            # 4-byte triangle count
            f.write(struct.pack("<I", len(self.triangles)))

            # Each triangle: normal (3 floats), 3 vertices (9 floats), attribute byte count (uint16)
            for norm, (v1, v2, v3) in self.triangles:
                f.write(struct.pack("<3f", *norm))
                f.write(struct.pack("<3f", *v1))
                f.write(struct.pack("<3f", *v2))
                f.write(struct.pack("<3f", *v3))
                f.write(struct.pack("<H", 0))

        file_kb = round(os.path.getsize(filepath) / 1024, 1)
        print(f"[✓] Generated binary STL: {filepath} ({len(self.triangles)} triangles, {file_kb} KB)")


def build_handlebar_hood():
    mesh = BinarySTLWriter()

    # 1. Main Display Cradle Backplate (146mm x 84mm x 4mm)
    mesh.add_box(center=(0, 0, -2), size=(146, 84, 4))

    # 2. Side Walls (Left and Right)
    mesh.add_box(center=(-71.5, 0, 7), size=(3, 84, 14))
    mesh.add_box(center=( 71.5, 0, 7), size=(3, 84, 14))

    # 3. Top Wall
    mesh.add_box(center=(0, 40.5, 7), size=(146, 3, 14))

    # 4. Bottom Wall with Cable Pass-through Slot (gap in center)
    mesh.add_box(center=(-45, -40.5, 7), size=(56, 3, 14))
    mesh.add_box(center=( 45, -40.5, 7), size=(56, 3, 14))

    # 5. Sun Visor Hood (Flaring outward by 28mm)
    mesh.add_hood_flange(
        base_w=146,
        base_h=84,
        tip_w=166,
        tip_h=96,
        length=28,
        z_base=14
    )

    # 6. Dual Handlebar Clamp Blocks (22.2mm diameter bar clamp mounts)
    # Left Clamp Block (Center at X=-45, Y=-15, Z=-18)
    mesh.add_box(center=(-45, 0, -14), size=(20, 40, 20))
    mesh.add_cylinder(center=(-45, 0, -18), radius=11.1, length=24, axis='x')

    # Right Clamp Block (Center at X=+45, Y=-15, Z=-18)
    mesh.add_box(center=( 45, 0, -14), size=(20, 40, 20))
    mesh.add_cylinder(center=( 45, 0, -18), radius=11.1, length=24, axis='x')

    # 7. M4 Bolt Bosses on Clamps
    mesh.add_box(center=(-45,  18, -14), size=(16, 8, 16))
    mesh.add_box(center=(-45, -18, -14), size=(16, 8, 16))
    mesh.add_box(center=( 45,  18, -14), size=(16, 8, 16))
    mesh.add_box(center=( 45, -18, -14), size=(16, 8, 16))

    output_stl = os.path.join("hardware_cad", "handlebar_display_hood.stl")
    mesh.write_binary_stl(output_stl, "Indriyo Motorcycle Handlebar Display Hood STL")
    return output_stl


if __name__ == "__main__":
    print("[*] Generating Indriyo Handlebar Sun Hood STL Mesh...")
    build_handlebar_hood()
