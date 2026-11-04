"""Regression checks for v0.6 retry and attachment durability."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import importlib.util
import sys
ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'reliable_notify'
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
retry = load('retry')
classify_error, validate_policies = retry.classify_error, retry.validate_policies
media = load('media')
snapshot_attachments, cleanup_media, free_disk_bytes = media.snapshot_attachments, media.cleanup_media, media.free_disk_bytes
QueueStore = load('store').QueueStore


class RetryPolicyTest(unittest.TestCase):
    def test_default_and_custom(self):
        p = validate_policies({'critical': {'max_attempts': 0, 'base_seconds': 10}})
        self.assertEqual(p['critical']['base_seconds'], 10)
        self.assertEqual(p['warning']['max_attempts'], 20)
        with self.assertRaises(ValueError):
            validate_policies({'info': {'base_seconds': 4000}})
        with self.assertRaises(ValueError):
            validate_policies({'info': {'max_attempts': True}})

    def test_failure_classes(self):
        self.assertEqual(classify_error(ValueError('bad')).kind, 'invalid_payload')
        self.assertFalse(classify_error(ValueError('bad')).retryable)
        self.assertTrue(classify_error(TimeoutError('timeout')).retryable)
        self.assertEqual(classify_error(Exception('Forbidden: chat not found')).kind, 'authentication')
        http = Mock(status=429)
        http.__str__ = lambda _: 'Retry after 42'
        result = classify_error(http)
        self.assertEqual((result.kind, result.retry_after), ('rate_limit', 42))


class DurableAttachmentTest(unittest.TestCase):
    def test_attachments_copied_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            from unittest.mock import patch
            base = Path(tmp)
            source = base / 'reports' / 'report.pdf'
            source.parent.mkdir()
            source.write_bytes(b'first report')
            spool = base / 'reliable_notify'
            with patch.object(media, 'MEDIA_ROOT', base):
                converted, refs = snapshot_attachments({'attachments': [{'path': str(source)}]},
                                                       str(spool), min_free_bytes=0)
                self.assertEqual(len(refs), 1)
                self.assertIn('/reliable_notify/', converted['attachments'][0]['media_source']['media_content_id'])
                source.write_bytes(b'updated report')
                self.assertEqual(Path(refs[0]).read_bytes(), b'first report')
                cleanup_media(str(spool), set(refs))
                self.assertTrue(Path(refs[0]).exists())
                cleanup_media(str(spool), set())
                self.assertFalse(Path(refs[0]).exists())

    def test_reject_outside_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'secrets.txt'
            src.write_text('SECRET')
            with self.assertRaises(ValueError):
                snapshot_attachments({'attachments': [{'path': str(src)}]}, tmp,
                                     min_free_bytes=0)
            self.assertEqual(len(list(Path(tmp).glob('*.txt'))), 1)


class StoreMigrationTest(unittest.TestCase):
    def test_multiple_media_references_survive_retry(self):
        async def run():
            with tempfile.TemporaryDirectory() as tmp:
                q = QueueStore(Path(tmp) / 'queue.db')
                record = {'message': 'test', 'target': 'notify.test', 'priority': 'info',
                          'ttl': 0, 'dedup_key': None, 'strategy': 'always',
                          'action': 'smtp.send_message', 'payload': {},
                          'media_paths': ['/media/reliable_notify/a.pdf', '/media/reliable_notify/b.png']}
                ids = await q.enqueue_many([record], 100)
                self.assertEqual(len(ids), 1)
                self.assertEqual(len(await q.pending_media_paths()), 2)
                await q.failed(ids[0], 1, 'bad', 1, permanent=True, category='invalid_payload')
                self.assertEqual(len(await q.pending_media_paths()), 2)
                self.assertEqual(await q.retry_one(ids[0], dead=True), 1)
                self.assertEqual(len(await q.pending_media_paths()), 2)
                await q.delete_one(ids[0] + 1)
                self.assertEqual(await q.pending_media_paths(), set())
        asyncio.run(run())


if __name__ == '__main__':
    unittest.main()