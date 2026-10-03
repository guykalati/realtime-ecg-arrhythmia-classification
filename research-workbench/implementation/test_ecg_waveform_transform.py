import unittest

import numpy as np

from ecg_waveform_transform import apply, fit


class WaveformTransformTest(unittest.TestCase):
    def test_train_only_scaler_and_offset_invariance(self):
        t = np.linspace(0, 2 * np.pi, 360, dtype=np.float32)
        train = np.stack([np.sin(t), 2 * np.sin(t), 3 * np.cos(t)])
        external = np.stack([5 * np.sin(t) + 100, 8 * np.cos(t) - 50])
        for mode in ("centered", "robust"):
            parameters = fit(train, mode)
            self.assertAlmostEqual(apply(train, parameters).std(), 1.0, places=5)
            np.testing.assert_allclose(apply(external, parameters),
                                       apply(external - np.array([[100], [-50]]), parameters),
                                       atol=2e-5)
            self.assertEqual(parameters, fit(train, mode))

    def test_flat_window_stays_finite(self):
        train = np.stack([np.arange(360, dtype=np.float32),
                          np.zeros(360, dtype=np.float32)])
        transformed = apply(train, fit(train, "robust"))
        self.assertTrue(np.isfinite(transformed).all())
        self.assertTrue(np.all(transformed[1] == 0))


if __name__ == "__main__":
    unittest.main()
