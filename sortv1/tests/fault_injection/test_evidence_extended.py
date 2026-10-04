import tempfile
import unittest
from pathlib import Path
from app.evidence import Journal,EvidenceError
from app.tools.acceptance_record import record

class ExtendedEvidenceTests(unittest.TestCase):
    def test_rotation_replay_and_csv_preserve_count(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);j=Journal(p/'journal.jsonl','PHYSICAL',rotate_bytes=1,minimum_free_bytes=0)
            j.append('INSPECT',{'cycle_key':'b:1'});j.append('DONE',dict(cycle_key='b:1',boot='b',cycle=1,request=1,confirmed_bin=0,seq=1))
            replay=Journal(p/'journal.jsonl','PHYSICAL');self.assertEqual(replay.counts(),[1,0,0,0]);self.assertFalse(replay.pending_cycles())
            replay.export_csv(p/'export.csv');text=(p/'export.csv').read_text();self.assertIn('confirmed_bin',text);self.assertIn('b:1',text)
    def test_acceptance_rejects_simulated_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);file=p/'proof.txt';file.write_text('SYNTHETIC_TEST')
            data=dict(test_id='P01',hardware_revision='fixture',model_sha256='fixture',firmware_version='fixture',stimulus='fixture',expected='fixture',observed='fixture',result='PASS',evidence_path=str(file),operator='fixture',source='SIMULATION')
            with self.assertRaises(ValueError):record(data,Journal(p/'acceptance.jsonl','PHYSICAL'))
    def test_diagnostic_and_auto_counts_are_separate(self):
        with tempfile.TemporaryDirectory() as d:
            j=Journal(Path(d)/'j.jsonl','PHYSICAL',mode='DIAGNOSTIC')
            j.append('DONE',dict(cycle_key='b:1',confirmed_bin=0))
            j.append('DONE',dict(cycle_key='b:2',confirmed_bin=1,mode='PHYSICAL_AUTO'))
            self.assertEqual(j.counts('DIAGNOSTIC'),[1,0,0,0]);self.assertEqual(j.counts('PHYSICAL_AUTO'),[0,1,0,0])
if __name__=='__main__':unittest.main()
