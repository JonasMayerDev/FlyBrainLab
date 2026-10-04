import hashlib, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from scripts.kb_store import LocalKnowledgeBase
from scripts.discovery_tools import read_source_snapshot

class SnapshotTests(unittest.TestCase):
    def test_real_hash_before_html_reading_text_and_pagination(self):
        with tempfile.TemporaryDirectory() as directory:
            kb=LocalKnowledgeBase(directory)
            html='<html><head><script>hidden()</script><style>badcss</style></head><body><p>'+'Evidence &amp; conditions. '*12+'</p></body></html>'
            row=kb.add_source({'url':'https://example.org/paper','title':'Fixture evidence','source_kind':'paper','retrieval_status':'retrieved','dataset_version':'fixture','publication_date':'2026','limitations':['fixture only']},html)
            with patch('scripts.discovery_tools.LocalKnowledgeBase',return_value=kb):
                first=read_source_snapshot(row['source_id'],100)
                second=read_source_snapshot(row['source_id'],100,100)
                self.assertEqual(first['content_sha256'],hashlib.sha256(html.encode()).hexdigest())
                self.assertNotIn('hidden',first['content']); self.assertNotIn('badcss',first['content'])
                self.assertIn('Evidence & conditions.',first['content'])
                self.assertTrue(first['truncated']); self.assertEqual(second['offset'],100)
                snapshot=Path(directory)/row['snapshot_path']
                snapshot.write_text(html+'tampered')
                with self.assertRaisesRegex(ValueError,'hash mismatch'):read_source_snapshot(row['source_id'],100)
