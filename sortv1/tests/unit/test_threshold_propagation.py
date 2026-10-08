import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from training.thresholds import selection, load_selection, copy_selected, runtime_values
from training.evaluate.metrics import metrics
from app.utils import write_json, sha256

class ThresholdPropagationTests(unittest.TestCase):
    def test_nonbaseline_preserved_and_hashed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); checkpoint=p/"ckpt"; manifest=p/"manifest"
            checkpoint.write_bytes(b"checkpoint"); manifest.write_text("manifest")
            path=p/"selected.json"; write_json(path,selection(0.73,0.21,checkpoint,manifest))
            value=load_selection(path,checkpoint,manifest)
            out=p/"package"; out.mkdir(); hashes=copy_selected(path,checkpoint,manifest,out)
            self.assertEqual((out/"threshold_selection.json").read_bytes(),path.read_bytes())
            self.assertEqual(json.loads((out/"thresholds.json").read_text()),runtime_values(value))
            self.assertEqual(hashes["thresholds.json"],sha256(out/"thresholds.json"))
            scores=np.array([[.75,.12,.08,.05]])
            self.assertEqual(metrics([0],[0],scores,top1=value["top1_min_exclusive"],margin=value["margin_min_exclusive"])["coverage"],1)
            self.assertEqual(metrics([0],[0],scores)["coverage"],0)
            manifest.write_text("changed")
            with self.assertRaisesRegex(ValueError,"binding changed"): load_selection(path,checkpoint,manifest)
    def test_fail_closed_status_source_values(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); ck=p/"ck"; mf=p/"mf"; ck.write_text("a");mf.write_text("b");path=p/"s.json"
            for changes in ({"status":"NO_CANDIDATE_MEETS_PURITY"},{"split":"test"},{"source":"SYNTHETIC_TEST"},{"top1_min_exclusive":float("nan")},{"frames_required":1},{"consensus_required":3}):
                path.write_text(json.dumps({**selection(.9,.2,ck,mf),**changes}))
                with self.assertRaises(ValueError): load_selection(path,ck,mf)
            write_json(path,selection(.73,.21,ck,mf,status="TECHNICAL_FIXTURE",source="SYNTHETIC_TEST"))
            with self.assertRaises(ValueError):load_selection(path,ck,mf)
            self.assertEqual(load_selection(path,ck,mf,technical_smoke=True)["status"],"TECHNICAL_FIXTURE")
if __name__=="__main__":unittest.main()
