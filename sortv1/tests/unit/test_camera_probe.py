import unittest
import numpy as np
from app.tools.camera_probe import quantities
class CameraProbeTests(unittest.TestCase):
    def test_measured_units(self):
        background=np.full((5,5,3),50,dtype=np.uint8)
        values=quantities(np.full_like(background,80),background)
        self.assertEqual(values,dict(mean=80,laplacian_variance=0,clipped_fraction=0,presence_difference=30))
        values=quantities(np.full_like(background,255),background)
        self.assertEqual(values['clipped_fraction'],1)
    def test_bad_shape_blocks(self):
        with self.assertRaises(ValueError):quantities(np.zeros((2,2,3),np.uint8),np.zeros((2,2,3),np.uint8))
        with self.assertRaises(ValueError):quantities(np.zeros((5,5,3),np.uint8),np.zeros((4,5,3),np.uint8))
