import unittest
from core.biomechanics import calculate_angle_3d, get_hand_joint_angles, detect_hand_view

class DummyPoint:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class TestBiomechanics(unittest.TestCase):
    def test_calculate_angle_3d_straight(self):
        # Straight line: (0, 1) -> (0, 0) -> (0, -1) should be 180 degrees
        p1 = DummyPoint(0.0, 1.0, 0.0)
        p2 = DummyPoint(0.0, 0.0, 0.0)
        p3 = DummyPoint(0.0, -1.0, 0.0)
        angle = calculate_angle_3d(p1, p2, p3)
        self.assertAlmostEqual(angle, 180.0, places=1)

    def test_calculate_angle_3d_right_angle(self):
        # Right angle: (1, 0) -> (0, 0) -> (0, 1) should be 90 degrees
        p1 = DummyPoint(1.0, 0.0, 0.0)
        p2 = DummyPoint(0.0, 0.0, 0.0)
        p3 = DummyPoint(0.0, 1.0, 0.0)
        angle = calculate_angle_3d(p1, p2, p3)
        self.assertAlmostEqual(angle, 90.0, places=1)

    def test_calculate_angle_3d_zero_distance(self):
        # Overlapping points should safely return 180.0 without division by zero
        p1 = DummyPoint(0.0, 0.0, 0.0)
        p2 = DummyPoint(0.0, 0.0, 0.0)
        p3 = DummyPoint(1.0, 0.0, 0.0)
        angle = calculate_angle_3d(p1, p2, p3)
        self.assertEqual(angle, 180.0)

    def test_get_hand_joint_angles(self):
        # Create 21 points in a straight line
        landmarks = [DummyPoint(0.0, float(i), 0.0) for i in range(21)]
        angles = get_hand_joint_angles(landmarks)
        self.assertIn("Index", angles)
        self.assertIn("Thumb", angles)
        self.assertIn("Middle", angles)
        self.assertIn("Ring", angles)
        self.assertIn("Pinky", angles)
        
        # Check separate MCP, PIP, and DIP joint keys
        self.assertIn("Index_MCP", angles)
        self.assertIn("Index_PIP", angles)
        self.assertIn("Index_DIP", angles)
        self.assertIn("Thumb_MCP", angles)
        self.assertIn("Thumb_IP", angles)
        self.assertIn("View", angles)

        # Straight points should have angles close to 180
        self.assertAlmostEqual(angles["Index_PIP"], 180.0, places=1)
        self.assertAlmostEqual(angles["Index_DIP"], 180.0, places=1)

    def test_detect_hand_view(self):
        # Front view: knuckles (Index MCP 5 and Pinky MCP 17) spread wide
        front_lms = [DummyPoint(0.0, 0.0, 0.0) for _ in range(21)]
        front_lms[0] = DummyPoint(0.5, 0.9)  # Wrist
        front_lms[5] = DummyPoint(0.3, 0.5)  # Index MCP
        front_lms[9] = DummyPoint(0.5, 0.5)  # Middle MCP
        front_lms[17] = DummyPoint(0.7, 0.5) # Pinky MCP
        self.assertEqual(detect_hand_view(front_lms), "FRONT")

        # Lateral view: knuckles compressed horizontally (feed multiple frames for rolling buffer)
        lat_lms = [DummyPoint(0.0, 0.0, 0.0) for _ in range(21)]
        lat_lms[0] = DummyPoint(0.5, 0.9)
        lat_lms[5] = DummyPoint(0.51, 0.5)
        lat_lms[9] = DummyPoint(0.5, 0.5)
        lat_lms[17] = DummyPoint(0.52, 0.5)
        res = "FRONT"
        for _ in range(6):
            res = detect_hand_view(lat_lms)
        self.assertEqual(res, "LATERAL")

if __name__ == "__main__":
    unittest.main()
