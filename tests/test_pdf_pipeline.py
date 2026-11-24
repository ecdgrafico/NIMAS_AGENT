import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "nimas-agent"))

from create_pdf_project import classify
from validate_ai_proposal import validate

class PdfPipelineTests(unittest.TestCase):
    def test_filename_classification(self):
        self.assertEqual(classify("book_FM.pdf"), "frontmatter")
        self.assertEqual(classify("book_L01.pdf"), "bodymatter")
        self.assertEqual(classify("book_EM.pdf"), "rearmatter")
        self.assertEqual(classify("book_scan.pdf"), "unclassified")

    def test_proposal_validator_accepts_fragment(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "unit.xml"
            path.write_text('<level1><h1>Lesson 1</h1><p>Text.</p></level1>', encoding="utf-8")
            self.assertEqual(validate(path)["status"], "pass")

    def test_proposal_validator_rejects_package_root(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "unit.xml"
            path.write_text('<dtbook><book/></dtbook>', encoding="utf-8")
            result = validate(path)
            self.assertEqual(result["status"], "fail")
            self.assertTrue(result["errors"])

if __name__ == "__main__":
    unittest.main()
