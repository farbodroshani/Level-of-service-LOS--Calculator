"""Checks the calculators against the HCM 7th Edition Chapter 26 example problems.

Run with:  python -m unittest discover tests
"""
import unittest

from los_calculator import calculate_freeway, calculate_multilane, calculate_two_lane, design_for_target_los
from los_calculator.two_lane import horizontal_class, vertical_class
from los_calculator.uninterrupted import specific_grade_pce

TWO_LANE_BASE = dict(segment_type="Passing Constrained", length=0.75, grade=0, posted_speed=50, volume=752,
                     phf=0.94, hv=5, lane_width=12, shoulder_width=6, access_points=0, curves="")


class FreewayExamples(unittest.TestCase):
    def test_example_1_four_lane_freeway(self):
        r = calculate_freeway(dict(volume=2000, phf=0.92, lanes=2, trucks=5, terrain="Level", lane_width=11,
                                   lateral_clearance=2, ramp_density=4))
        self.assertAlmostEqual(r["FFS (mi/h)"], 60.8, delta=0.05)
        self.assertEqual(r["Capacity (pc/h/ln)"], 2308)
        self.assertAlmostEqual(r["vp (pc/h/ln)"], 1142, delta=1)
        self.assertAlmostEqual(r["Density (pc/mi/ln)"], 18.8, delta=0.05)
        self.assertEqual(r["LOS"], "C")

    def test_example_2_lanes_for_target_los(self):
        r = design_for_target_los(dict(volume=4000, phf=0.85, trucks=8, terrain="Level", lane_width=12,
                                       lateral_clearance=6, ramp_density=3), "Freeway", "D")
        self.assertEqual(r["lanes_required"], 3)
        self.assertAlmostEqual(r["result"]["Speed (mi/h)"], 65.4, delta=0.05)
        self.assertAlmostEqual(r["result"]["Density (pc/mi/ln)"], 25.9, delta=0.05)

    def test_example_3_six_lane_freeway(self):
        expected = {5000: (64.7, 29.0, "D"), 5788: (59.1, 36.7, "E")}
        for volume, (speed, density, los) in expected.items():
            r = calculate_freeway(dict(volume=volume, phf=0.96, lanes=3, trucks=4, terrain="Rolling",
                                       measured_ffs=70))
            self.assertAlmostEqual(r["Speed (mi/h)"], speed, delta=0.05)
            self.assertAlmostEqual(r["Density (pc/mi/ln)"], density, delta=0.05)
            self.assertEqual(r["LOS"], los)

    def test_example_6_severe_weather(self):
        r = calculate_freeway(dict(volume=2000, phf=0.92, lanes=2, trucks=5, terrain="Rolling", lane_width=11,
                                   lateral_clearance=2, ramp_density=4, saf=0.86, caf=0.78))
        self.assertAlmostEqual(r["FFSadj (mi/h)"], 52.3, delta=0.05)
        self.assertEqual(r["Capacity (pc/h/ln)"], 1734)
        self.assertAlmostEqual(r["Speed (mi/h)"], 52.3, delta=0.1)

    def test_demand_above_capacity_is_los_f(self):
        r = calculate_freeway(dict(volume=9000, phf=0.9, lanes=2, trucks=5, terrain="Level", lane_width=12,
                                   lateral_clearance=6, ramp_density=1))
        self.assertEqual(r["LOS"], "F")


class MultilaneExamples(unittest.TestCase):
    def test_example_4_five_lane_highway_on_grade(self):
        cases = {"EB": (-3.5, 10, 49.5, 2.24, 18.1), "WB": (3.5, 0, 52.0, 3.97, 18.8)}
        for grade, apd, ffs, et, density in cases.values():
            r = calculate_multilane(dict(volume=1500, phf=0.90, lanes=2, trucks=6, terrain="Specific grade",
                                         grade=grade, grade_length=1.25, truck_mix="30% SUT / 70% TT", bffs=52,
                                         lane_width=12, right_clearance=12, left_clearance=12,
                                         access_points=apd, median="TWLTL"))
            self.assertAlmostEqual(r["FFS (mi/h)"], ffs, delta=0.05)
            self.assertAlmostEqual(r["ET"], et, delta=0.005)
            self.assertAlmostEqual(r["Density (pc/mi/ln)"], density, delta=0.1)
            self.assertEqual(r["LOS"], "C")

    def test_specific_grade_pce_interpolation(self):
        self.assertAlmostEqual(specific_grade_pce(3.5, 1.25, 6, "30% SUT / 70% TT"), 3.97)
        self.assertAlmostEqual(specific_grade_pce(-5, 1.25, 6, "30% SUT / 70% TT"), 2.24)


class TwoLaneExamples(unittest.TestCase):
    def test_example_1_passing_constrained(self):
        r = calculate_two_lane(dict(TWO_LANE_BASE))
        self.assertAlmostEqual(r["FFS (mi/h)"], 56.83, delta=0.01)
        self.assertAlmostEqual(r["Average speed (mi/h)"], 53.7, delta=0.05)
        self.assertAlmostEqual(r["Percent followers (%)"], 67.7, delta=0.05)
        self.assertAlmostEqual(r["Follower density (followers/mi/ln)"], 10.1, delta=0.05)
        self.assertEqual(r["LOS"], "D")

    def test_example_2_horizontal_curves(self):
        inputs = dict(TWO_LANE_BASE, curves="450,3,432; 300,2,366.5; 275,5,216; 750,0,458; 1100,4,767.9")
        r = calculate_two_lane(inputs)
        self.assertAlmostEqual(r["Average speed (mi/h)"], 49.5, delta=0.1)

    def test_example_3_passing_lane(self):
        r = calculate_two_lane(dict(TWO_LANE_BASE, segment_type="Passing Lane", length=1.5, posted_speed=55,
                                    volume=825, phf=0.95, hv=8))
        self.assertAlmostEqual(r["Percent followers (%)"], 60.7, delta=0.05)
        self.assertAlmostEqual(r["FD at end (followers/mi/ln)"], 9.1, delta=0.05)
        self.assertAlmostEqual(r["Follower density (followers/mi/ln)"], 2.9, delta=0.05)
        self.assertEqual(r["LOS"], "B")

    def test_example_3_downstream_of_passing_lane(self):
        r = calculate_two_lane(dict(TWO_LANE_BASE, length=1.0, posted_speed=55, volume=820, phf=0.95, hv=8,
                                    pl_length=1.5, pl_distance=2.5, pl_pf_in=69.7, pl_flow_in=904))
        self.assertAlmostEqual(r["Follower density (followers/mi/ln)"], 8.2, delta=0.06)
        self.assertEqual(r["LOS"], "D")

    def test_classification_tables(self):
        self.assertEqual(vertical_class(0.75, 0), 1)
        self.assertEqual(vertical_class(0.8, -5), 4)
        self.assertEqual(vertical_class(0.3, 6), 3)
        self.assertEqual(horizontal_class(450, 3), 3)
        self.assertEqual(horizontal_class(1100, 4), 1)
        self.assertEqual(horizontal_class(2600, 0), 0)

    def test_demand_above_capacity_is_los_f(self):
        r = calculate_two_lane(dict(TWO_LANE_BASE, segment_type="Passing Zone", volume=1700, opposing_volume=500,
                                    phf=0.9))
        self.assertEqual(r["LOS"], "F")


if __name__ == "__main__":
    unittest.main()
