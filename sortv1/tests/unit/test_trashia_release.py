import io
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts import fetch_trashia
from scripts.inspect_trashia_inference import sanitized_response


class TrashiaReleaseTests(unittest.TestCase):
    def test_public_metadata_does_not_imply_api_or_dataset_access(self):
        # Isolate the public-only case from an operator's already-downloaded local dataset.
        public = (fetch_trashia.METADATA / 'public_metadata.json').read_bytes()
        with tempfile.TemporaryDirectory() as directory, patch.object(fetch_trashia, 'METADATA', Path(directory)):
            (Path(directory) / 'public_metadata.json').write_bytes(public)
            record = fetch_trashia.initial_metadata()
        self.assertEqual(record['metadata_access'], 'PUBLIC_METADATA_VERIFIED')
        self.assertEqual(record['license'], 'CC BY 4.0')
        self.assertEqual(record['dataset_export_access'], 'ACCESS_REQUIRED')
        self.assertFalse(record['dataset_downloaded'])
        self.assertIsNone(record['class_ids'])

    def test_hosted_response_discards_secrets_headers_and_urls(self):
        record = sanitized_response({'predictions': [{'class': '0', 'class_id': 0, 'confidence': .9,
            'x': 2, 'y': 3, 'authorization': 'fixture-credential', 'url': 'https://host/?signature=fixture'}],
            'headers': {'Authorization': 'fixture-credential'}, 'image': {'width': 40, 'height': 40},
            'signed_url': 'https://host/?signature=fixture'}, 'fixture-credential')
        self.assertEqual(record['predictions'][0]['class'], '0')
        self.assertNotIn('fixture-credential', str(record))
        self.assertNotIn('https://', str(record))
        with self.assertRaises(ValueError):
            sanitized_response({'predictions': [{'class': 'fixture-credential'}]}, 'fixture-credential')

    def test_export_archive_sha_and_safe_paths(self):
        content = io.BytesIO()
        with zipfile.ZipFile(content, 'w') as archive:
            archive.writestr('train/annotation.json', '{"categories": []}')
        from hashlib import sha256
        api = types.SimpleNamespace(get_version_export=lambda *args: {'export': {'link': 'https://download.invalid/export'}})
        fake = {'roboflow': types.ModuleType('roboflow'), 'roboflow.adapters': types.SimpleNamespace(rfapi=api)}
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, fake), \
                patch.object(fetch_trashia, 'ROOT', Path(directory)), \
                patch.object(fetch_trashia.urllib.request, 'urlopen', return_value=io.BytesIO(content.getvalue())):
            destination = Path(directory) / 'data'
            digest = fetch_trashia.download_export(types.SimpleNamespace(version=1), 'fixture-credential', 'coco', destination)
            self.assertEqual(digest, sha256(content.getvalue()).hexdigest())
            self.assertTrue((destination / 'train/annotation.json').is_file())

    def test_zip_traversal_is_rejected_before_extract(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'unsafe.zip'
            with zipfile.ZipFile(archive, 'w') as handle:
                handle.writestr('../outside.txt', 'fixture')
            with self.assertRaises(ValueError):
                fetch_trashia.safe_extract(archive, Path(directory) / 'data')
            self.assertFalse((Path(directory) / 'outside.txt').exists())
