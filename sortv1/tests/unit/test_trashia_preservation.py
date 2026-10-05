import contextlib
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts import fetch_trashia as fetch


class TrashiaPreservationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.metadata = self.root / 'sortv1/training/datasets/roboflow'
        self.metadata.mkdir(parents=True)
        self.dataset = self.root / 'sortv1/training/datasets/external/trashia/1'
        self.dataset.mkdir(parents=True)
        (self.dataset / 'fixture.txt').write_bytes(b'dataset fixture, not physical acceptance')
        self.public = dict(workspace='trashia', project='trashia', status='PUBLIC_METADATA_VERIFIED',
            selected_version=1, versions=[1], task_type='object-detection', license='CC BY 4.0',
            classes=['0', '1', '2', '3', '4', '5'], export_sha256=None)
        self.previous = dict(self.public, status='DATASET_DOWNLOADED', dataset_downloaded=True,
            dataset_export_access='DATASET_EXPORT_VERIFIED', metadata_access='MANUAL_EXPORT_VERIFIED',
            export_sha256='a' * 64)
        self.files = [dict(path='fixture.txt', sha256=hashlib.sha256((self.dataset/'fixture.txt').read_bytes()).hexdigest(),
                           bytes=(self.dataset/'fixture.txt').stat().st_size)]
        self.manifest = dict(workspace='trashia', project='trashia', version=1, source='EXTERNAL',
            status='DATASET_DOWNLOADED', files=self.files, export_sha256='a' * 64)
        for name, data in [('public_metadata.json', self.public), ('trashia_metadata.json', self.previous),
                           ('source_manifest.json', self.manifest)]:
            self.write(name, data)
        for name, value in [('ROOT', self.root), ('METADATA', self.metadata)]:
            patcher = patch.object(fetch, name, value); patcher.start(); self.addCleanup(patcher.stop)
        environment = patch.dict(os.environ, {}, clear=True); environment.start(); self.addCleanup(environment.stop)

    def write(self, name, data):
        (self.metadata / name).write_text(json.dumps(data), encoding='utf-8')

    def read(self, name='trashia_metadata.json'):
        return json.loads((self.metadata / name).read_text())

    def read_full(self):
        return json.loads(fetch.full_manifest_path(1).read_text())

    def run_cli(self, *args):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            code = fetch.main(list(args))
        return code, stream.getvalue()

    def fake_api(self, *, fails=False):
        secret = os.environ['ROBOFLOW_API_KEY']
        def workspace(*args, **kwargs):
            print(secret)
            logging.error('fixture SDK leak %s', secret)
            if fails:
                raise RuntimeError('Authorization Bearer ' + secret + ' https://host/?signature=' + secret)
            version = types.SimpleNamespace(version=2, preprocessing={}, augmentation={}, images=100, splits={})
            project = types.SimpleNamespace(type='object-detection', classes=['0','1','2','3','4','5'],
                versions=lambda: [version], images=100, splits={})
            return types.SimpleNamespace(project=lambda *args: project)
        module = types.ModuleType('roboflow')
        module.Roboflow = lambda **kwargs: types.SimpleNamespace(workspace=workspace)
        adapters = types.ModuleType('roboflow.adapters')
        adapters.rfapi = types.SimpleNamespace(get_project=lambda *args: {'project': {'license':'CC BY 4.0',
            'Authorization': secret, 'signed_url':'https://host/?signature=' + secret}})
        return patch.dict(sys.modules, {'roboflow': module, 'roboflow.adapters': adapters})

    def test_a_downloaded_state_survives_inspection_without_api_key(self):
        code, _ = self.run_cli('--inspect-only')
        self.assertEqual(code, 0)
        state = self.read()
        self.assertEqual(state['status'], 'DATASET_DOWNLOADED')
        for field in ('selected_version','dataset_downloaded','dataset_export_access','metadata_access'):
            self.assertEqual(state[field], self.previous[field])

    def test_b_inspection_preserves_existing_index(self):
        self.run_cli('--inspect-only')
        self.assertEqual(self.read_full()['files'], self.files)
        self.assertNotIn('files', self.read('source_manifest.json'))

    def test_c_reindex_is_offline_and_scoped_to_pinned_version(self):
        old = dict(self.public, status='METADATA_ACCESS_VERIFIED', dataset_downloaded=False,
                   metadata_access='METADATA_ACCESS_VERIFIED', dataset_export_access='ACCESS_REQUIRED')
        self.write('trashia_metadata.json', old)
        self.write('source_manifest.json', dict(self.manifest, files=[], export_sha256=None))
        other = self.dataset.parent/'2'; other.mkdir(); (other/'other.txt').write_text('other version')
        original = (self.dataset/'fixture.txt').read_bytes()
        with patch.object(fetch, 'download_export', side_effect=AssertionError('No download permitted')):
            code, _ = self.run_cli('--reindex-existing', '--version', '1')
        self.assertEqual(code, 0)
        state = self.read(); index = self.read('source_manifest.json')
        self.assertTrue(state['dataset_downloaded'])
        self.assertEqual(state['selected_version'], 1)
        self.assertEqual(self.read_full()['files'], self.files)
        self.assertEqual(index['file_count'], len(self.files))
        self.assertEqual(index['status'], 'REINDEXED_EXISTING_DATASET')
        self.assertIsNone(state['export_sha256'])
        self.assertEqual((self.dataset/'fixture.txt').read_bytes(), original)

    def test_d_missing_dataset_does_not_publish_downloaded(self):
        self.write('trashia_metadata.json', self.public)
        before = (self.metadata/'trashia_metadata.json').read_bytes()
        code, _ = self.run_cli('--reindex-existing', '--version', '99')
        self.assertEqual(code, 2)
        self.assertEqual((self.metadata/'trashia_metadata.json').read_bytes(), before)
        self.assertIsNot(self.read().get('dataset_downloaded'), True)

    def test_e_known_export_sha_survives_inspection_and_reindex(self):
        self.run_cli('--inspect-only')
        self.assertEqual(self.read()['export_sha256'], 'a' * 64)
        self.assertEqual(self.read('source_manifest.json')['export_sha256'], 'a' * 64)
        self.run_cli('--reindex-existing', '--version', '1')
        self.assertEqual(self.read()['export_sha256'], 'a' * 64)

    def test_verified_fields_survive_api_inspection_of_another_version(self):
        for downloaded in (False, True):
            previous = dict(self.previous, dataset_downloaded=downloaded,
                            status='DATASET_DOWNLOADED' if downloaded else 'METADATA_ACCESS_VERIFIED')
            self.write('trashia_metadata.json', previous)
            with patch.dict(os.environ, {'ROBOFLOW_API_KEY': 'fixture-private-credential'}), self.fake_api():
                code, _ = self.run_cli('--inspect-only', '--version', '2')
            self.assertEqual(code, 0)
            for field in fetch.INSPECTION_STATE_FIELDS:
                self.assertEqual(self.read().get(field), previous.get(field))
            self.assertEqual(self.read_full()['files'], self.files)
            if downloaded:
                self.assertEqual(self.read()['status'], 'DATASET_DOWNLOADED')

    def test_f_no_credentials_in_metadata_manifest_stdout_or_logs(self):
        with patch.dict(os.environ, {'ROBOFLOW_API_KEY': 'fixture-private-credential'}):
            for fails in (False, True):
                logs = io.StringIO(); handler = logging.StreamHandler(logs)
                logging.getLogger().addHandler(handler)
                try:
                    with self.fake_api(fails=fails):
                        _, output = self.run_cli('--inspect-only')
                finally:
                    logging.getLogger().removeHandler(handler)
                saved = ''.join(p.read_text() for p in self.root.rglob('*.json'))
                for text in (saved, output, logs.getvalue()):
                    self.assertNotIn('fixture-private-credential', text)
                    self.assertNotIn('Authorization', text)
                    self.assertNotIn('signature=', text)
                self.assertTrue(self.read()['dataset_downloaded'])
                self.assertEqual(self.read_full()['files'], self.files)

    def test_existing_dataset_never_downloads_automatically(self):
        before = (self.metadata/'trashia_metadata.json').read_bytes()
        with patch.object(fetch, 'download_export', side_effect=AssertionError('No download permitted')):
            code, _ = self.run_cli('--version', '1', '--format', 'coco')
        self.assertEqual(code, 2)
        self.assertEqual((self.metadata/'trashia_metadata.json').read_bytes(), before)

    def test_explicit_cache_zip_is_verified_before_hash_recovery(self):
        self.write('trashia_metadata.json', dict(self.previous, export_sha256=None))
        self.write('source_manifest.json', dict(self.manifest, export_sha256=None))
        cache = self.root/'datasets-cache'; cache.mkdir(); archive = cache/'original.zip'
        with zipfile.ZipFile(archive, 'w') as handle:
            handle.write(self.dataset/'fixture.txt', 'fixture.txt')
        code, _ = self.run_cli('--reindex-existing', '--version', '1', '--export-zip', str(archive))
        self.assertEqual(code, 0)
        self.assertEqual(self.read()['export_sha256'], hashlib.sha256(archive.read_bytes()).hexdigest())
        with zipfile.ZipFile(archive, 'w') as handle:
            handle.writestr('fixture.txt', 'different dataset')
        before = (self.metadata/'source_manifest.json').read_bytes()
        code, _ = self.run_cli('--reindex-existing', '--version', '1', '--export-zip', str(archive))
        self.assertEqual(code, 2)
        self.assertEqual((self.metadata/'source_manifest.json').read_bytes(), before)

    def test_reviewed_mapping_and_manual_report_are_not_overwritten(self):
        mapping = self.root/'sortv1/training/datasets/class_mapping.yaml'
        text = "status: REVIEWED\ndefault: CHALLENGE_OOD\nclasses:\n" + ''.join(
            f"  '{name}': {{target: CHALLENGE_OOD, reviewed: true}}\n" for name in self.public['classes'])
        mapping.write_text(text)
        report = self.root/'docs/ml/TRASHIA_MAPPING_REPORT.md'; report.parent.mkdir(parents=True)
        report.write_text('manual review evidence')
        self.run_cli('--inspect-only')
        self.assertEqual(mapping.read_text(), text)
        self.assertEqual(report.read_text(), 'manual review evidence')

    def test_manifest_a_reindex_writes_full_manifest_in_local_cache(self):
        code, _ = self.run_cli('--reindex-existing', '--version', '1')
        self.assertEqual(code, 0)
        artifact = self.root/'datasets-cache/trashia-manifests/source_manifest_v1_full.json'
        self.assertTrue(artifact.is_file())
        self.assertFalse(artifact.is_relative_to(self.metadata))

    def test_manifest_b_full_manifest_contains_every_file(self):
        nested = self.dataset/'train'; nested.mkdir()
        (nested/'second.bin').write_bytes(b'second fixture')
        (nested/'empty.txt').write_bytes(b'')
        expected = sorted([dict(path=p.relative_to(self.dataset).as_posix(),
            sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)
            for p in self.dataset.rglob('*') if p.is_file()], key=lambda item: item['path'])
        self.run_cli('--reindex-existing', '--version', '1')
        self.assertEqual(self.read_full()['files'], expected)
        self.assertEqual(self.read_full()['version'], 1)

    def test_manifest_c_tracked_summary_excludes_file_list(self):
        self.run_cli('--reindex-existing', '--version', '1')
        summary = self.read('source_manifest.json')
        self.assertNotIn('files', summary)
        required = {'workspace', 'project', 'version', 'source', 'status', 'dataset_downloaded',
                    'file_count', 'total_bytes', 'full_manifest_sha256', 'export_sha256', 'index_status',
                    'generated_from'}
        self.assertTrue(required.issubset(summary))
        self.assertLess((self.metadata/'source_manifest.json').stat().st_size, 2048)

    def test_manifest_d_summary_has_exact_file_count(self):
        self.run_cli('--reindex-existing', '--version', '1')
        self.assertEqual(self.read('source_manifest.json')['file_count'], len(self.files))

    def test_manifest_e_summary_has_exact_total_bytes(self):
        self.run_cli('--reindex-existing', '--version', '1')
        self.assertEqual(self.read('source_manifest.json')['total_bytes'], sum(p['bytes'] for p in self.files))

    def test_manifest_f_summary_hashes_full_artifact_bytes(self):
        self.run_cli('--reindex-existing', '--version', '1')
        artifact = fetch.full_manifest_path(1)
        self.assertEqual(self.read('source_manifest.json')['full_manifest_sha256'],
                         hashlib.sha256(artifact.read_bytes()).hexdigest())

    def test_manifest_g_inspection_preserves_summary_offline_and_with_api_failure(self):
        self.run_cli('--reindex-existing', '--version', '1')
        before = (self.metadata/'source_manifest.json').read_bytes()
        artifact = fetch.full_manifest_path(1).read_bytes()
        self.assertEqual(self.run_cli('--inspect-only')[0], 0)
        self.assertEqual((self.metadata/'source_manifest.json').read_bytes(), before)
        for fails in (False, True):
            with patch.dict(os.environ, {'ROBOFLOW_API_KEY': 'fixture-private-credential'}), self.fake_api(fails=fails):
                code, _ = self.run_cli('--inspect-only', '--version', '2')
            self.assertEqual(code, 2 if fails else 0)
            self.assertEqual((self.metadata/'source_manifest.json').read_bytes(), before)
            self.assertEqual(fetch.full_manifest_path(1).read_bytes(), artifact)
            self.assertTrue(self.read()['dataset_downloaded'])

    def test_manifest_h_credentials_are_refused_before_artifacts_are_written(self):
        with patch.dict(os.environ, {'ROBOFLOW_API_KEY': 'fixture-private-credential'}):
            code, output = self.run_cli('--reindex-existing', '--version', '1')
            self.assertEqual(code, 0)
            before = {p: p.read_bytes() for p in self.root.rglob('*.json')}
            (self.dataset/'fixture-private-credential.txt').write_text('untrusted source filename')
            code, rejected = self.run_cli('--reindex-existing', '--version', '1')
            self.assertEqual(code, 2)
            for path, contents in before.items():
                self.assertEqual(path.read_bytes(), contents)
                self.assertNotIn(b'fixture-private-credential', contents)
                self.assertNotIn(b'Authorization', contents)
                self.assertNotIn(b'signature=', contents)
            self.assertNotIn('fixture-private-credential', output + rejected)

    def test_repeated_reindex_produces_identical_summary_and_full_bytes(self):
        self.run_cli('--reindex-existing', '--version', '1')
        full = fetch.full_manifest_path(1).read_bytes()
        summary = (self.metadata/'source_manifest.json').read_bytes()
        self.run_cli('--reindex-existing', '--version', '1')
        self.assertEqual(fetch.full_manifest_path(1).read_bytes(), full)
        self.assertEqual((self.metadata/'source_manifest.json').read_bytes(), summary)
        self.assertNotIn(b'\r\n', full)
        self.assertNotIn(b'\r\n', summary)

    def test_inspection_preserves_summary_when_cache_artifact_is_absent(self):
        self.run_cli('--reindex-existing', '--version', '1')
        summary = (self.metadata/'source_manifest.json').read_bytes()
        fetch.full_manifest_path(1).unlink()
        with patch.object(fetch, 'index_files', side_effect=AssertionError('No dataset traversal permitted')):
            code, _ = self.run_cli('--inspect-only')
        self.assertEqual(code, 0)
        self.assertEqual((self.metadata/'source_manifest.json').read_bytes(), summary)
        self.assertTrue(self.read()['dataset_downloaded'])
        self.assertFalse(fetch.full_manifest_path(1).exists())
