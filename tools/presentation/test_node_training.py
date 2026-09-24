from __future__ import annotations

import unittest

from node_training_view import adapt_page


class NodeViewTests(unittest.TestCase):
    def test_mount_preserves_nonce_and_payloads_and_localizes_navigation(self):
        page = (
            '<html><head></head><body><script nonce="abc">'
            "const demoToken=\"bound-token\";fetch('/api/status');"
            "fetch('/api/run', {method: \"POST\", headers: { 'X-Demo-Token': demoToken },"
            "});</script></body></html>"
        )
        for lang, title in (("en", "Node training example"), ("ru", "Обучение узлов")):
            result = adapt_page(page, lang)
            self.assertIn(title, result)
            self.assertIn(f"/admin/?lang={lang}#/live-execution", result)
            self.assertIn('nonce="abc"', result)
            self.assertIn('const demoToken="bound-token"', result)
            self.assertIn("fetch('/node-training/api/run'", result)
            self.assertIn("'Content-Type': 'application/json'", result)
            self.assertIn("body: '{}'", result)
            self.assertNotIn("fetch('/api/", result)
            self.assertIn("LOCAL_DEMO_ONLY", result)


if __name__ == "__main__":
    unittest.main()
