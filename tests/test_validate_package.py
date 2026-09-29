import tempfile
import unittest
from pathlib import Path

from scripts.validate_package import validate


class ValidatePackageTests(unittest.TestCase):
    def test_reports_broken_local_markdown_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "afp-style"
            (root / "agents").mkdir(parents=True)
            (root / "SKILL.md").write_text(
                '---\nname: afp-style\ndescription: "A useful news photo skill"\n---\n',
                encoding="utf-8",
            )
            (root / "agents/openai.yaml").write_text(
                'interface:\n'
                '  display_name: "AFP 助手"\n'
                '  short_description: "生成或转绘法新社风格新闻纪实图，并规划报道配图方案"\n'
                '  default_prompt: "用 $afp-style 生成图片。"\n',
                encoding="utf-8",
            )
            (root / "README.md").write_text("[Broken link](missing.md)\n", encoding="utf-8")

            errors = validate(root)
            self.assertTrue(any("missing link target 'missing.md'" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
