"""Tests for the hand handling in live_probe (lift_hand, place_hand)."""
import math
import sys
import types
import unittest
from unittest.mock import patch

# live_probe installs the ctypes ONNX Runtime shim at import, which needs the QNX
# library. CI has no onnxruntime at all: a stand-in module during the import makes
# the shim step aside, as probe_frame_test does. Nothing here runs a model.
with patch.dict(sys.modules, {"onnxruntime": types.ModuleType("onnxruntime")}):
    from percept.tools import live_probe as lp

W, H = 1280, 720
BOTTLE = {"name": "bottle", "in_latest_boxes": True, "bbox_px": [600, 200, 700, 500],
          "xyz_cam": [0.0, 0.0, 0.6]}


def world(hand_box, objects, target="bottle"):
    return {"hand": {"bbox_px": hand_box, "xyz_cam": [0.0, 0.0, 2.5]},
            "objects": objects, "target": {"name": target}}


class LiftHandTest(unittest.TestCase):
    def test_watch_marks_the_hand_and_is_not_findable(self):
        w = {"t_ns": 1, "objects": [dict(BOTTLE), {"name": "watch", "conf": 0.3, "bbox_px": [1, 2, 3, 4]}]}
        out, hand = lp.lift_hand(w)
        self.assertEqual(hand["bbox_px"], [1, 2, 3, 4])
        self.assertEqual([o["name"] for o in out["objects"]], ["bottle"])

    def test_a_real_hand_wins_over_a_watch(self):
        w = {"t_ns": 1, "objects": [{"name": "watch", "conf": 0.5, "bbox_px": [1, 1, 2, 2]},
                                    {"name": "hand", "conf": 0.1, "bbox_px": [9, 9, 10, 10]}]}
        _, hand = lp.lift_hand(w)
        self.assertEqual(hand["bbox_px"], [9, 9, 10, 10])

    def test_no_hand_leaves_the_world_alone(self):
        w = {"objects": [dict(BOTTLE)]}
        out, hand = lp.lift_hand(w)
        self.assertIsNone(hand)
        self.assertIs(out, w)


class HandLookalikeTest(unittest.TestCase):
    def test_hand_boxed_as_bottle_is_dropped(self):
        fake = {"name": "bottle", "in_latest_boxes": True, "bbox_px": [100, 100, 300, 300]}
        w = {"hand": {"bbox_px": [110, 110, 300, 290]}, "objects": [fake, dict(BOTTLE)]}
        self.assertEqual([o["bbox_px"] for o in lp.drop_hand_lookalikes(w)["objects"]], [BOTTLE["bbox_px"]])

    def test_gripped_bottle_is_kept(self):
        # hand over the middle of a tall bottle: overlap is partial
        w = {"hand": {"bbox_px": [590, 300, 690, 380]}, "objects": [dict(BOTTLE)]}
        self.assertEqual(len(lp.drop_hand_lookalikes(w)["objects"]), 1)


class PlaceHandTest(unittest.TestCase):
    def dist(self, w):
        return math.dist(lp.place_hand(w, W, H, 60.0)["hand"]["xyz_cam"], BOTTLE["xyz_cam"])

    def test_hand_on_the_object_reads_zero(self):
        self.assertAlmostEqual(self.dist(world([620, 250, 720, 350], [dict(BOTTLE)])), 0.0)

    def test_hand_beside_the_object_reads_its_gap(self):
        # hand centre 55 px right of the box edge at 0.6 m: 55 / f * 0.6, f = 640 / tan(30 deg)
        f = 640 / math.tan(math.radians(30))
        self.assertAlmostEqual(self.dist(world([705, 300, 805, 400], [dict(BOTTLE)])), 55 / f * 0.6, places=4)

    def test_free_hand_is_kept_within_arms_reach(self):
        hand = lp.place_hand(world([100, 100, 200, 200], [dict(BOTTLE)]), W, H, 60.0)["hand"]
        self.assertAlmostEqual(hand["xyz_cam"][2], lp.HAND_MAX_Z_M)

    def test_input_is_not_modified(self):
        w = world([620, 250, 720, 350], [dict(BOTTLE)])
        lp.place_hand(w, W, H, 60.0)
        self.assertEqual(w["hand"]["xyz_cam"], [0.0, 0.0, 2.5])


if __name__ == "__main__":
    unittest.main()
