from __future__ import annotations

import math
import unittest

from richmack_framework import (
    adjusted_wpm,
    approach_score,
    approach_total,
    capability_gap,
    days_for_growth,
    effective_progress,
    entropy_cost,
    generic_growth,
    growth_from_raw_reps,
    growth_multiplier,
    independence,
    information_density,
    information_mass,
    learning_unit_components,
    learning_unit_strict,
    leakage,
    leakage_from_rate,
    net_information_mass,
    per_rep_improvement,
    readiness,
    refresh_unit,
    refresh_unit_connected,
    raw_reps_for_stable,
    stable_reps,
    stable_reps_for_growth,
    target_multiplier,
    seven_rep_growth,
)


class ImprovementFormulaTests(unittest.TestCase):

    def test_seven_reps_double_capability(self):
        self.assertAlmostEqual(
            seven_rep_growth(
                1,
                7,
            ),
            2.0,
        )

    def test_fourteen_reps_quadruple_capability(self):
        self.assertAlmostEqual(
            growth_multiplier(
                14
            ),
            4.0,
        )

    def test_forty_nine_reps_equal_128x(self):
        self.assertAlmostEqual(
            growth_multiplier(
                49
            ),
            128.0,
        )

    def test_reps_for_100x(self):
        self.assertAlmostEqual(
            stable_reps_for_growth(
                100
            ),
            46.506993,
            places=5,
        )

    def test_days_for_growth(self):
        self.assertAlmostEqual(
            days_for_growth(
                4,
                2,
            ),
            7.0,
        )

    def test_per_rep_improvement(self):
        self.assertAlmostEqual(
            per_rep_improvement(),
            0.1040895,
            places=6,
        )

    def test_generic_growth(self):
        self.assertAlmostEqual(
            generic_growth(
                100,
                0.10,
                2,
            ),
            121.0,
        )


class StabilityTests(unittest.TestCase):

    def test_stable_reps(self):
        self.assertEqual(
            stable_reps(
                0.5,
                40,
            ),
            20,
        )

    def test_raw_reps_for_stable(self):
        self.assertEqual(
            raw_reps_for_stable(
                20,
                0.5,
            ),
            40,
        )

    def test_leakage(self):
        self.assertEqual(
            leakage(
                40,
                18,
            ),
            22,
        )

    def test_leakage_from_rate(self):
        self.assertAlmostEqual(
            leakage_from_rate(
                40,
                0.45,
            ),
            22.0,
        )

    def test_growth_uses_stable_reps(self):
        self.assertAlmostEqual(
            growth_from_raw_reps(
                1,
                0.5,
                14,
            ),
            2.0,
        )


class ApproachTests(unittest.TestCase):

    def test_approach_score(self):
        self.assertAlmostEqual(
            approach_score(
                0.9,
                0.8,
                0.7,
                0.6,
            ),
            0.3024,
        )

    def test_approach_total(self):
        self.assertEqual(
            approach_total(
                [1, 2, 3]
            ),
            6,
        )


class LearningUnitTests(unittest.TestCase):

    def test_learning_unit_components(self):
        self.assertEqual(
            learning_unit_components(
                1,
                1,
                1,
            ),
            3,
        )

    def test_strict_learning_unit_complete(self):
        self.assertEqual(
            learning_unit_strict(
                True,
                True,
                True,
            ),
            1,
        )

    def test_strict_learning_unit_incomplete(self):
        self.assertEqual(
            learning_unit_strict(
                True,
                True,
                False,
            ),
            0,
        )

    def test_refresh_unit(self):
        self.assertEqual(
            refresh_unit(
                3
            ),
            1,
        )

    def test_connected_refresh_unit(self):
        self.assertEqual(
            refresh_unit_connected(
                1,
                1,
                1,
            ),
            1,
        )


class InformationTests(unittest.TestCase):

    def test_mass_zero_bits(self):
        self.assertEqual(
            information_mass(
                0,
                10,
            ),
            0,
        )

    def test_mass_formula(self):
        expected = (
            10
            * math.log(11)
            * 4
        )

        self.assertAlmostEqual(
            information_mass(
                10,
                3,
            ),
            expected,
        )

    def test_net_mass(self):
        self.assertEqual(
            net_information_mass(
                100,
                20,
            ),
            80,
        )

    def test_density(self):
        self.assertEqual(
            information_density(
                100,
                20,
            ),
            5,
        )


class CapabilityTests(unittest.TestCase):

    def test_gap(self):
        self.assertEqual(
            capability_gap(
                100,
                40,
            ),
            60,
        )

    def test_target_multiplier(self):
        self.assertEqual(
            target_multiplier(
                100,
                25,
            ),
            4,
        )

    def test_independence(self):
        self.assertEqual(
            independence(
                6,
                10,
            ),
            0.6,
        )

    def test_readiness(self):
        self.assertAlmostEqual(
            readiness(
                0.8,
                0.9,
                0.75,
            ),
            0.54,
        )


class FocusTests(unittest.TestCase):

    def test_no_entropy_under_three_items(self):
        self.assertEqual(
            entropy_cost(
                3
            ),
            0,
        )

    def test_entropy_above_three_items(self):
        self.assertEqual(
            entropy_cost(
                6
            ),
            3,
        )

    def test_effective_progress(self):
        self.assertEqual(
            effective_progress(
                10,
                3,
            ),
            7,
        )

    def test_adjusted_wpm(self):
        self.assertEqual(
            adjusted_wpm(
                60,
                5,
            ),
            55,
        )


class ValidationTests(unittest.TestCase):

    def test_invalid_retention(self):
        with self.assertRaises(
            ValueError
        ):
            stable_reps(
                1.5,
                10,
            )

    def test_zero_baseline_multiplier(self):
        with self.assertRaises(
            ValueError
        ):
            target_multiplier(
                10,
                0,
            )

    def test_density_zero_bits(self):
        with self.assertRaises(
            ValueError
        ):
            information_density(
                10,
                0,
            )


if __name__ == "__main__":
    unittest.main()
