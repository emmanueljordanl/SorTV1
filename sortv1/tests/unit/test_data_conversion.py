import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from app.utils import sha256
from training.datasets.convert_detection_to_classification import convert
from training.datasets.validate import validate_manifest,write_rows
from training.tools.prepare_dataset import prepare

class DataConversionTests(unittest.TestCase):
    def test_unknown_mapping_and_original_grouping(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);rgb=np.random.default_rng(42).integers(0,255,(40,40,3),dtype=np.uint8);Image.fromarray(rgb).save(p/'x.png')
            coco=dict(images=[dict(id=1,file_name='x.png')],categories=[dict(id=1,name='reviewed_pet'),dict(id=2,name='ambiguous_plastic')],
                annotations=[dict(id=1,image_id=1,category_id=1,bbox=[0,0,20,20]),dict(id=2,image_id=1,category_id=2,bbox=[20,20,20,20]),dict(id=3,image_id=1,category_id=1,bbox=[0,0,2,2])])
            (p/'coco.json').write_text(json.dumps(coco));mapping={'default':'CHALLENGE_OOD','classes':{'reviewed_pet':{'target':'PET','reviewed':True,'reason':'catalogue reviewed'}}}
            rows=convert(p/'coco.json',p,p/'crops',mapping,'1');self.assertEqual(len(rows),2)
            self.assertEqual({r['split'] for r in rows},{'challenge'});self.assertEqual(len({r['object_id'] for r in rows}),2)
            self.assertEqual(len({r['source_image_id'] for r in rows}),1);self.assertEqual(validate_manifest(p/'crops/manifest.csv',strict=True),2)
            mapping['classes']['reviewed_pet']['reviewed']=False
            with self.assertRaisesRegex(ValueError,'Unreviewed'):convert(p/'coco.json',p,p/'other',mapping,'1')
    def test_freeze_change_does_not_overwrite_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);image=p/'x.png';Image.new('RGB',(8,8),(10,20,30)).save(image)
            row=dict(object_id='a',session_id='s',class_id='0',split='test',image_path=str(image),source='LOCAL_PHYSICAL',source_dataset='tray',source_version='s',source_image_id='a',sha256=sha256(image),lighting_setup='l',operator='o',excluded_reason='')
            src=p/'src.csv';out=p/'prepared.csv';write_rows(src,[row]);prepare([src],out,allow_auxiliary_only=True);original=out.read_bytes()
            row['object_id']='changed';write_rows(src,[row])
            with self.assertRaisesRegex(ValueError,'Frozen TEST changed'):prepare([src],out,allow_auxiliary_only=True)
            self.assertEqual(out.read_bytes(),original)
if __name__=='__main__':unittest.main()
