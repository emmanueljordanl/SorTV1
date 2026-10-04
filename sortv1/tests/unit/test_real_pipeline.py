import csv
import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from app.contracts import Cycle,Frame
from app.quality.image_quality import ImageQuality
from app.inference.preprocessing import DEFAULT,tensor_rgb,softmax
from app.inference.onnx_runtime import OnnxInference
from app.utils import sha256,write_json
from training.datasets.validate import FIELDS,write_rows,validate_manifest

class RealPipelineTests(unittest.TestCase):
    def test_preprocess_rgb_contract_and_nonfinite(self):
        image=np.zeros((10,20,3),dtype=np.uint8);image[:,:,0]=255
        t=tensor_rgb(image,DEFAULT)
        self.assertEqual(t.shape,(1,3,224,224));self.assertEqual(t.dtype,np.float32)
        self.assertGreater(t[0,0,112,112],t[0,2,112,112])
        with self.assertRaises(ValueError):softmax(np.array([[np.nan,0,0,0]]))
        with self.assertRaises(ValueError):softmax(np.zeros((1,5)))

    def quality(self):
        return ImageQuality(dict(max_age_ms=300,presence_difference_min=2,laplacian_variance_min=1,mean_min=5,mean_max=250,clipped_fraction_max=0.8),np.full((10,10,3),50,dtype=np.uint8))
    def test_empty_stale_wrong_cycle_repeat(self):
        c=Cycle('b',1);q=self.quality();empty=np.full((10,10,3),50,dtype=np.uint8)
        self.assertEqual(q.assess(Frame('f',c,1,empty,{}),c,2,weight_present=True).reason,'EMPTY_TRAY')
        self.assertEqual(q.assess(Frame('f2',c,1,empty,{}),c,400_000_001,weight_present=True).reason,'STALE_FRAME')
        self.assertEqual(q.assess(Frame('f3',Cycle('b',2),2,empty,{}),c,3,weight_present=True).reason,'WRONG_CYCLE')
        self.assertEqual(q.assess(Frame('f4',c,3,empty,{}),c,4,weight_present=True).reason,'REPEATED_FRAME')
        self.assertEqual(q.assess(Frame('f5',c,4,None,{}),c,5,weight_present=True).reason,'NO_IMAGE')
    def test_unmeasured_quality_blocks(self):
        with self.assertRaises(ValueError):ImageQuality({})
    def test_model_missing_hash_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            package=Path(directory)
            with self.assertRaises(FileNotFoundError):OnnxInference(package)
            write_json(package/'model_manifest.json',{'sha256':{}})
            with self.assertRaisesRegex(ValueError,'Incomplete'):OnnxInference(package)
            files=['model.onnx','labels.json','preprocess.json','thresholds.json','training.json','dataset_manifest.csv']
            for f in files:(package/f).write_text('[]')
            hashes={f:sha256(package/f) for f in files};write_json(package/'model_manifest.json',{'sha256':hashes})
            (package/'model.onnx').write_text('modified')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):OnnxInference(package)

    def test_leakage_object_source_and_hash(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'manifest.csv'
            base=dict(object_id='a',session_id='s',class_id='0',split='train',image_path='a.png',source='LOCAL_PHYSICAL',source_dataset='SorTV1',source_version='s',source_image_id='original',sha256='abc',lighting_setup='l',operator='o',excluded_reason='')
            for key in ['object_id','source_image_id','sha256']:
                other={**base,'object_id':'b','source_image_id':'other','sha256':'def','split':'test','image_path':'b.png',key:base[key]}
                write_rows(path,[base,other])
                with self.assertRaisesRegex(ValueError,'Fuga'):validate_manifest(path)
            write_rows(path,[base,{**base,'object_id':'b','source_image_id':'other','image_path':'b.png'}])
            with self.assertRaisesRegex(ValueError,'Duplicate image hash'):validate_manifest(path)
    def test_real_image_hash_and_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);image=p/'image.png';Image.new('RGB',(8,8),(10,20,30)).save(image)
            row=dict(object_id='a',session_id='s',class_id='0',split='train',image_path='image.png',source='LOCAL_PHYSICAL',source_dataset='tray',source_version='s',source_image_id='a',sha256=sha256(image),lighting_setup='l',operator='o',excluded_reason='')
            write_rows(p/'manifest.csv',[row]);self.assertEqual(validate_manifest(p/'manifest.csv',strict=True),1)
            image.write_bytes(b'corrupted');row['sha256']=sha256(image);write_rows(p/'manifest.csv',[row])
            with self.assertRaises(OSError):validate_manifest(p/'manifest.csv',strict=True)

if __name__=='__main__':unittest.main()
