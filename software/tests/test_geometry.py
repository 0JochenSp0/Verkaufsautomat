import copy
import unittest

import _paths  # noqa: F401
import geometry as g


class GeometryTest(unittest.TestCase):
    def setUp(self):
        self.p = g.load_params()
        self.a = g.allowances_from(self.p)

    def test_default_layout_meets_min_target(self):
        L = g.layout(self.p)
        self.assertGreaterEqual(L.total_positions, 10, "Ziel min. 10 Positionen")
        self.assertTrue(L.fits_height)
        self.assertTrue(L.window_ok)

    def test_universal_is_min_of_products(self):
        L = g.layout(self.p)
        self.assertEqual(L.sectors_per_level, min(L.sectors_egg, L.sectors_jar))

    def test_monotonic_in_diameter(self):
        prev = 0
        for D in range(300, 700, 10):
            n = g.layout(self.p, diameter=D).sectors_per_level
            self.assertGreaterEqual(n, prev, f"D={D}")
            prev = n

    def test_reference_values_from_plan(self):
        # Table in docs/konzept.md §2 (125x98 carton, jar Ø85)
        expect = {380: (8, 3), 420: (9, 4), 450: (10, 5)}
        egg = g.Rect(125, 98)
        jar = g.Circle(85)
        a = g.Allowances(wall=4, clearance=5, rim_margin=0, hub_radius=30)
        for D, (n_jar, n_egg) in expect.items():
            R = D / 2 - 10
            self.assertEqual(g.sectors_for_circle(R, jar, a), n_jar, D)
            self.assertEqual(g.sectors_for_rect(R, egg, a), n_egg, D)

    def test_jar_fits_geometrically_in_chosen_wedge(self):
        L = g.layout(self.p)
        R = L.diameter / 2
        r = self.p["products"]["honey_jar"]["diameter"] / 2
        c = R - self.a.rim_margin - self.a.clearance - r
        half = (L.sector_angle_deg / 2) * 3.141592653589793 / 180
        import math
        self.assertGreaterEqual(c * math.sin(half), r + self.a.wall / 2 + self.a.clearance - 1e-6)

    def test_too_small_returns_zero(self):
        self.assertEqual(g.sectors_for_rect(60, g.Rect(125, 98), self.a), 0)
        self.assertEqual(g.sectors_for_circle(50, g.Circle(85), self.a), 0)

    def test_explicit_sector_count_above_max_rejected(self):
        p = copy.deepcopy(self.p)
        p["carousel"]["sectors_per_level"] = 50
        with self.assertRaises(ValueError):
            g.layout(p)

    def test_diameter_limited_by_depth_or_width(self):
        p = copy.deepcopy(self.p)
        p["fridge_inner"]["depth"] = 300
        self.assertEqual(g.carousel_diameter(p), 300 - 25 - 12)


if __name__ == "__main__":
    unittest.main()
