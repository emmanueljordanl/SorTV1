import time
import unittest
import numpy as np
from app.capture.picamera2_capture import PicameraCapture
from app.contracts import Cycle

class Request:
    def __init__(self,stamp):self.stamp=stamp;self.released=False
    def get_metadata(self):return {'SensorTimestamp':self.stamp,'ExposureTime':0,'AnalogueGain':1.0}
    def make_array(self,name):return np.full((8,10,3),50,dtype=np.uint8)
    def release(self):self.released=True
class Camera:
    def __init__(self):self.requests=[];self.initial=True
    def create_video_configuration(self,**kwargs):return kwargs
    def configure(self,c):self.config=c
    def start(self):pass
    def capture_request(self,**kwargs):return kwargs
    def wait(self,job,timeout):
        assert job['flush'] is True
        stamp=time.clock_gettime_ns(time.CLOCK_BOOTTIME) if hasattr(time,'CLOCK_BOOTTIME') else time.monotonic_ns()
        if self.initial:stamp-=1_000_000_000;self.initial=False
        r=Request(stamp);self.requests.append(r);return r
    def stop(self):pass
    def close(self):pass
class CameraTests(unittest.TestCase):
    def test_fresh_exposures_and_release_and_roi(self):
        cfg=dict(size=[10,8],fps=15,spacing_ms=10,settle_ms=0,timeout_s=1,controls={},locked=True,roi=[1,1,5,4]);fake=Camera();c=PicameraCapture(cfg,camera=fake)
        cycle=Cycle('b',1);frames=[c.capture(cycle) for _ in range(3)]
        self.assertEqual(frames[0].rgb.shape,(4,5,3));self.assertEqual(len({f.frame_id for f in frames}),3)
        self.assertGreaterEqual(frames[1].captured_ns-frames[0].captured_ns,10_000_000)
        self.assertTrue(all(r.released for r in fake.requests));self.assertEqual(len(fake.requests),4)
    def test_uncalibrated_blocks(self):
        with self.assertRaises(ValueError):PicameraCapture({'locked':False},camera=Camera())
if __name__=='__main__':unittest.main()
