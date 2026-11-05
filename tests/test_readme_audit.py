"""repo-ready readme_audit.py: length budget and plain-language rules. Run: python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins/repo-ready/engine"))

import readme_audit

CLEAN = """# foo

Size-capped, rotated logs for Python apps in one call.

```bash
pip install foo
```

## How it works

1. Set a disk budget.
2. Foo rotates files by size.
"""


class AuditTextTest(unittest.TestCase):
    def test_clean_readme_passes(self):
        self.assertEqual(readme_audit.audit_text(CLEAN), [])

    def test_slop_is_flagged(self):
        text = "# foo\n\nA powerful tool — not just a linter \U0001f680. VERY IMPORTANT stuff.\n"
        found = " ".join(readme_audit.wording_issues(text))
        for marker in ("filler: powerful", "'not just X'", "long dash", "emoji", "caps"):
            self.assertIn(marker, found)

    def test_cluster_words_flag_only_in_pairs(self):
        self.assertEqual(readme_audit.wording_issues("# foo\n\nIt is very small.\n"), [])
        found = " ".join(readme_audit.wording_issues("# foo\n\nIt is very small\nand fully typed.\n"))
        self.assertIn("filler cluster: fully, very", found)

    def test_image_url_with_parentheses_is_one_url(self):
        text = "![MIT](https://img.shields.io/badge/license-MIT%20(code)-blue.svg)"
        self.assertEqual(readme_audit.MARKDOWN_IMAGE.findall(text), ["https://img.shields.io/badge/license-MIT%20(code)-blue.svg"])

    def test_sentence_wrapped_over_two_lines_is_one_sentence(self):
        line = " ".join(["word"] * 15)
        found = " ".join(readme_audit.wording_issues(f"# foo\n\n{line}\n{line}.\n"))
        self.assertIn("sentence over 25 words", found)

    def test_long_paragraph_and_list_and_nesting(self):
        para = "\n".join(["One short line here."] * 6)
        items = "\n".join(f"- item {i}" for i in range(9)) + "\n  - nested"
        found = " ".join(readme_audit.length_issues(f"# foo\n\n{para}\n\n{items}\n"))
        self.assertIn("paragraph of 6 lines", found)
        self.assertIn("list of 9 items", found)
        self.assertIn("nested list", found)

    def test_code_and_details_do_not_count_toward_budget(self):
        code = "```\n" + "x\n" * 300 + "```\n"
        folded = "<details>\n" + "".join(f"Line {i}.\n\n" for i in range(200)) + "</details>\n"
        self.assertEqual(readme_audit.audit_text(CLEAN + code + folded), [])

    def test_section_over_budget(self):
        body = "".join(f"Line {i}.\n\n" for i in range(25))
        found = " ".join(readme_audit.length_issues(f"# foo\n\n## Big\n\n{body}"))
        self.assertIn("section 'Big' has 25 lines", found)


if __name__ == "__main__":
    unittest.main()
