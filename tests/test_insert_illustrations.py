import unittest

from scripts.insert_illustrations import insert_illustrations


class InsertIllustrationsTests(unittest.TestCase):
    def setUp(self):
        self.article = "# Report\n\nFirst paragraph with an anchor.\n\nSecond paragraph.\n"

    def test_inserts_after_whole_paragraph_and_labels_ai_image(self):
        result = insert_illustrations(self.article, [{
            "anchor": "First paragraph", "position": "after",
            "image_path": "images/one image.webp", "caption": "The scene",
        }])
        self.assertIn(
            "First paragraph with an anchor.\n\n"
            "![The scene](images/one%20image.webp)\n"
            "*AI 生成示意图 · The scene*\n\nSecond paragraph.",
            result,
        )
        self.assertTrue(result.startswith("# Report\n\n"))

    def test_can_insert_before_a_heading(self):
        result = insert_illustrations(self.article, [{
            "anchor": "# Report", "position": "before", "image_path": "lead.webp",
        }])
        self.assertTrue(result.startswith("![AFP 风格配图 1](lead.webp)\n*AI 生成示意图*\n\n# Report"))

    def test_rejects_missing_or_ambiguous_anchor(self):
        for anchor, article in (("missing", self.article), ("paragraph", self.article * 2)):
            with self.subTest(anchor=anchor), self.assertRaisesRegex(ValueError, "Anchor"):
                insert_illustrations(article, [{"anchor": anchor, "image_path": "x.webp"}])

    def test_rejects_list_anchor_and_invalid_position(self):
        with self.assertRaisesRegex(ValueError, "lists"):
            insert_illustrations("- item\n", [{"anchor": "item", "image_path": "x.webp"}])
        with self.assertRaisesRegex(ValueError, "position"):
            insert_illustrations(self.article, [{"anchor": "First paragraph", "image_path": "x.webp", "position": "middle"}])

    def test_empty_manifest_preserves_source(self):
        self.assertEqual(insert_illustrations(self.article, []), self.article)


if __name__ == "__main__":
    unittest.main()
