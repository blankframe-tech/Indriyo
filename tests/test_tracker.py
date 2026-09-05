"""
Unit tests for Indriyo Multi-Object Vehicle Tracker.
"""

from indriyo_core.tracker import MultiObjectVehicleTracker, calculate_iou
from indriyo_core.detector import Detection


def test_iou_calculation():
    # Identical boxes
    assert calculate_iou((10, 10, 50, 50), (10, 10, 50, 50)) == 1.0
    # Completely disjoint
    assert calculate_iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0
    # 50% overlap approx
    iou = calculate_iou((0, 0, 20, 20), (10, 0, 30, 20))
    assert 0.3 < iou < 0.4


def test_tracker_association_and_smoothing():
    tracker = MultiObjectVehicleTracker(min_hits=1, max_age=3)
    
    # Frame 1
    d1 = [Detection(box=(100, 100, 200, 200), confidence=0.85, class_name="car", class_id=2)]
    tracks1 = tracker.update(d1, timestamp=1.0)
    assert len(tracks1) == 1
    tid = tracks1[0].track_id

    # Frame 2: Vehicle slightly moved
    d2 = [Detection(box=(105, 105, 205, 205), confidence=0.88, class_name="car", class_id=2)]
    tracks2 = tracker.update(d2, timestamp=1.05)
    assert len(tracks2) == 1
    assert tracks2[0].track_id == tid  # Track ID must persist
    assert tracks2[0].hits == 2


def test_tracker_deletion_on_timeout():
    tracker = MultiObjectVehicleTracker(min_hits=1, max_age=2)
    
    # Initialize track
    d1 = [Detection(box=(100, 100, 200, 200), confidence=0.85, class_name="car", class_id=2)]
    tracker.update(d1, timestamp=1.0)
    assert len(tracker.tracks) == 1

    # Update with empty detections for 3 frames (exceeding max_age=2)
    tracker.update([], timestamp=1.1)
    tracker.update([], timestamp=1.2)
    tracker.update([], timestamp=1.3)
    
    # Track should be purged
    assert len(tracker.tracks) == 0
