"""
Unit tests for Indriyo 3D Printable STL Mesh Generators.
Verifies file headers, triangle counts, and geometry validity.
"""

import os
import struct
from hardware_cad.generate_stl_mesh import build_dual_tail_pod
from hardware_cad.generate_hood_stl import build_handlebar_hood


def test_dual_pod_stl_generation(tmp_path):
    builder = build_dual_tail_pod()
    output_stl = str(tmp_path / "test_tail_pod.stl")
    builder.write_binary_stl(output_stl, header_text="Indriyo Dual Pod Test")

    assert os.path.exists(output_stl)
    file_size = os.path.getsize(output_stl)
    assert file_size > 84

    with open(output_stl, "rb") as f:
        header = f.read(80)
        assert b"Indriyo" in header
        num_triangles = struct.unpack("<I", f.read(4))[0]
        assert num_triangles > 200
        expected_size = 84 + (num_triangles * 50)
        assert file_size == expected_size


def test_handlebar_hood_stl_generation():
    output_path = build_handlebar_hood()
    assert os.path.exists(output_path)
    file_size = os.path.getsize(output_path)
    assert file_size > 84

    with open(output_path, "rb") as f:
        header = f.read(80)
        assert b"Indriyo" in header
        num_triangles = struct.unpack("<I", f.read(4))[0]
        assert num_triangles > 100
        expected_size = 84 + (num_triangles * 50)
        assert file_size == expected_size
