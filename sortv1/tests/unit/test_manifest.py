import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from training.datasets.validate import validate_manifest


class ManifestTests(unittest.TestCase):
    def test_repeated_object_cannot_cross_splits(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.csv"
            path.write_text("object_id,session_id,class_id,split,image_path,source,lighting_setup,operator,excluded_reason\n"
                            "o1,s1,0,train,a.png,PHYSICAL,led,A,\n"
                            "o1,s2,0,test,b.png,PHYSICAL,led,B,\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Fuga"):
                validate_manifest(path)
