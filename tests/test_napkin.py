"""system-design napkin.py: the worked 1M DAU chain and the verdict rungs. Run: python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins/system-design/skills/system-design/scripts"))

import napkin  # noqa: E402


class NapkinTest(unittest.TestCase):
    def test_one_million_dau_feed_fits_one_box(self):
        r = napkin.napkin(napkin.Assumptions(dau=1e6, req_per_user=20))
        self.assertAlmostEqual(r["avg_rps"], 231, delta=1)
        self.assertAlmostEqual(r["peak_rps"], 694, delta=1)
        self.assertEqual(r["servers"], 2)
        self.assertAlmostEqual(r["db_reads"], 125, delta=1)
        self.assertAlmostEqual(r["cache_bytes"] / 1e9, 7.2, delta=0.01)
        self.assertEqual((r["shards"], r["replicas"]), (1, 0))
        self.assertAlmostEqual(r["store_day"] / 1e9, 12, delta=0.01)
        self.assertIn("rungs 1-2", napkin.verdict(r)[0])

    def test_no_cache_at_scale_needs_replicas(self):
        r = napkin.napkin(napkin.Assumptions(dau=1e8, req_per_user=50, hit_rate=0))
        self.assertGreater(r["replicas"], 0)
        self.assertTrue(any("rung 7" in n for n in napkin.verdict(r)))

    def test_heavy_writes_need_shards(self):
        r = napkin.napkin(napkin.Assumptions(dau=1e8, req_per_user=100, read_share=0.5))
        self.assertGreater(r["shards"], 1)
        notes = napkin.verdict(r)
        self.assertFalse(any("one database" in n for n in notes))
        self.assertTrue(notes[-1].startswith("rung 7"), notes)

    def test_cli_rejects_share_above_one(self):
        with self.assertRaises(SystemExit):
            napkin.main(["--dau", "1000", "--req-per-user", "5", "--hit-rate", "1.5"])


if __name__ == "__main__":
    unittest.main()
