import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "dress_4140df311cf31024c3beb40f8af7c480"
SCRIPT = ROOT / "tools" / "build_structural_fields.py"


class DressExampleTest(unittest.TestCase):
    def test_reference_metadata_and_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "structural_fields.npz"
            subprocess.run(
                [sys.executable, str(SCRIPT), str(SAMPLE), str(output)],
                check=True,
            )
            with np.load(output) as result:
                self.assertEqual(result["struct_coord"].shape, (70678, 4))
                self.assertEqual(result["struct_valid_mask"].shape, (70678, 4))
                np.testing.assert_array_equal(result["struct_dim_valid"], True)
                np.testing.assert_array_equal(
                    result["anchor_vertex_counts"], [129, 1640, 193, 52]
                )
                np.testing.assert_allclose(
                    result["normalization_scale"],
                    [
                        1.1411020195030155,
                        0.7085343428113964,
                        0.8747442623299542,
                        1.0606297376157054,
                    ],
                    rtol=1e-10,
                    atol=1e-12,
                )
                fields = result["struct_coord"]
                mask = result["struct_valid_mask"]
                self.assertTrue(np.isfinite(fields[mask]).all())
                self.assertGreaterEqual(float(fields[mask].min()), 0.0)
                self.assertLessEqual(float(fields[mask].max()), 1.0)


if __name__ == "__main__":
    unittest.main()
