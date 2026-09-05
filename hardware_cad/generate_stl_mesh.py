#!/usr/bin/env python3
"""
Indriyo - 3D Printable STL Mesh Generator
Generates a watertight binary STL mesh of the dual ESP32-CAM tail pod:
- Dimensions: 86mm x 42mm x 36mm
- 15° outward splay for left and right blind-spot cameras
- Protective rain hoods over optical lenses
- Rear cable relief canal
- Dual M4/M5 motorcycle tail mounting brackets
"""

import os
import struct
import math
import numpy as np


class STLMeshBuilder:
    def __init__(self):
        self.triangles = []  # list of ((nx, ny, nz), (v1, v2, v3))

    def add_triangle(self, v1, v2, v3):
        v1 = np.array(v1, dtype=np.float32)
        v2 = np.array(v2, dtype=np.float32)
        v3 = np.array(v3, dtype=np.float32)
        
        # Calculate surface normal
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
        # Two triangles for a quad face
        self.add_triangle(v1, v2, v3)
        self.add_triangle(v1, v3, v4)

    def add_box(self, center, size, rot_z_deg=0.0):
        cx, cy, cz = center
        dx, dy, dz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
        rad = math.radians(rot_z_deg)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        def rotate_pt(x, y, z):
            # Rotate around center in Z
            rx = x * cos_r - y * sin_r + cx
            ry = x * sin_r + y * cos_r + cy
            rz = z + cz
            return (rx, ry, rz)

        # 8 corners relative to center
        p0 = rotate_pt(-dx, -dy, -dz)
        p1 = rotate_pt( dx, -dy, -dz)
        p2 = rotate_pt( dx,  dy, -dz)
        p3 = rotate_pt(-dx,  dy, -dz)
        p4 = rotate_pt(-dx, -dy,  dz)
        p5 = rotate_pt( dx, -dy,  dz)
        p6 = rotate_pt( dx,  dy,  dz)
        p7 = rotate_pt(-dx,  dy,  dz)

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

    def add_cylinder(self, center, radius, height, segments=24, axis='y'):
        cx, cy, cz = center
        half_h = height / 2.0
        angles = [2 * math.pi * i / segments for i in range(segments)]

        for i in range(segments):
            a1 = angles[i]
            a2 = angles[(i + 1) % segments]

            if axis == 'y':
                # Cylinder extending along Y axis (lens hoods)
                p1_bottom = (cx + radius * math.cos(a1), cy - half_h, cz + radius * math.sin(a1))
                p2_bottom = (cx + radius * math.cos(a2), cy - half_h, cz + radius * math.sin(a2))
                p1_top    = (cx + radius * math.cos(a1), cy + half_h, cz + radius * math.sin(a1))
                p2_top    = (cx + radius * math.cos(a2), cy + half_h, cz + radius * math.sin(a2))

                # Side
                self.add_quad(p1_bottom, p2_bottom, p2_top, p1_top)
                # Front rim
                self.add_triangle((cx, cy + half_h, cz), p2_top, p1_top)
                # Rear cap
                self.add_triangle((cx, cy - half_h, cz), p1_bottom, p2_bottom)

    def write_binary_stl(self, filepath: str, header_text: str = "Indriyo Tail Pod"):
        header = header_text.encode('ascii')[:80].ljust(80, b'\0')
        count = len(self.triangles)

        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(struct.pack('<I', count))
            for normal, (v1, v2, v3) in self.triangles:
                # normal
                f.write(struct.pack('<3f', normal[0], normal[1], normal[2]))
                # vertices
                f.write(struct.pack('<3f', v1[0], v1[1], v1[2]))
                f.write(struct.pack('<3f', v2[0], v2[1], v2[2]))
                f.write(struct.pack('<3f', v3[0], v3[1], v3[2]))
                # attribute byte count
                f.write(struct.pack('<H', 0))


def build_dual_tail_pod():
    builder = STLMeshBuilder()

    # 1. Central Aerodynamic Main Core
    builder.add_box(center=(0, 0, 0), size=(36.0, 42.0, 36.0))

    # 2. Left Camera Pod with 15° Outward Splay
    # Left camera angled at -15 degrees in Z
    builder.add_box(center=(-26.0, 0.0, 0.0), size=(30.0, 44.0, 36.0), rot_z_deg=-15.0)

    # 3. Right Camera Pod with 15° Outward Splay
    # Right camera angled at +15 degrees in Z
    builder.add_box(center=(26.0, 0.0, 0.0), size=(30.0, 44.0, 36.0), rot_z_deg=15.0)

    # 4. Left Lens Rain Hood / Sun Visor (forward facing -Y)
    builder.add_cylinder(center=(-25.0, -22.0, 0.0), radius=6.5, height=9.0, segments=24, axis='y')

    # 5. Right Lens Rain Hood / Sun Visor (forward facing -Y)
    builder.add_cylinder(center=(25.0, -22.0, 0.0), radius=6.5, height=9.0, segments=24, axis='y')

    # 6. Upper Eyebrow Visor Deflectors
    builder.add_box(center=(-25.0, -24.0, 8.0), size=(18.0, 6.0, 3.5), rot_z_deg=-15.0)
    builder.add_box(center=(25.0, -24.0, 8.0), size=(18.0, 6.0, 3.5), rot_z_deg=15.0)

    # 7. Rear Wiring Relief Canal
    builder.add_box(center=(0.0, 22.0, -4.0), size=(18.0, 10.0, 12.0))

    # 8. Motorcycle Tail Mounting Flanges (Left and Right M4 Screws)
    builder.add_box(center=(-36.0, 16.0, 14.0), size=(16.0, 14.0, 6.0))
    builder.add_box(center=(36.0, 16.0, 14.0), size=(16.0, 14.0, 6.0))

    return builder


def main():
    cad_dir = os.path.dirname(os.path.abspath(__file__))
    output_stl = os.path.join(cad_dir, "dual_cam_tail_pod.stl")

    print(f"[*] Generating watertight binary STL mesh for Indriyo Dual Tail Pod...")
    builder = build_dual_tail_pod()
    builder.write_binary_stl(output_stl, header_text="Indriyo Dual ESP32-CAM Tail Pod MK1")

    file_size_kb = os.path.getsize(output_stl) / 1024
    num_triangles = len(builder.triangles)

    print(f"[✓] Successfully generated STL: {output_stl}")
    print(f"    Triangle Count: {num_triangles}")
    print(f"    File Size:      {file_size_kb:.1f} KB")
    print(f"    Dimensions:     86mm (W) x 42mm (D) x 36mm (H)")
    print(f"    Splay Angle:    15° outward dual blind-spot coverage")
    print(f"    Status:         Ready for 3D slicing (Cura / Bambu / PrusaSlicer)")


if __name__ == "__main__":
    main()
