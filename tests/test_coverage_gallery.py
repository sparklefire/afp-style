import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parents[1]


class GalleryReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.copy_targets = []
        self.external_assets = []
        self.labels = []
        self.duplicates = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            if values["id"] in self.ids:
                self.duplicates.append(values["id"])
            self.ids.add(values["id"])
        if "data-copy" in values:
            self.copy_targets.append(values["data-copy"])
        if "aria-labelledby" in values:
            self.labels.extend(values["aria-labelledby"].split())
        if tag in {"script", "link", "img"}:
            for key in ("src", "href"):
                value = values.get(key, "")
                if value.startswith(("http://", "https://")):
                    self.external_assets.append(value)


class CoverageGalleryTests(unittest.TestCase):
    def test_copy_buttons_target_existing_text_and_gallery_is_offline(self):
        html = (ROOT / "gallery/coverage.html").read_text(encoding="utf-8")
        parser = GalleryReferences()
        parser.feed(html)
        self.assertEqual(len(parser.copy_targets), 3)
        self.assertTrue(set(parser.copy_targets) <= parser.ids)
        self.assertTrue(set(parser.labels) <= parser.ids)
        self.assertFalse(parser.duplicates)
        self.assertFalse(parser.external_assets)
        self.assertIn("构图示意", html)

    def test_gallery_links_in_skill_and_readme_resolve(self):
        target = ROOT / "gallery/coverage.html"
        for document in (ROOT / "SKILL.md", ROOT / "README.md"):
            self.assertIn("gallery/coverage.html", document.read_text(encoding="utf-8"))
        self.assertTrue(target.is_file())


if __name__ == "__main__":
    unittest.main()
