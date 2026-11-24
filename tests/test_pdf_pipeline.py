import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "nimas-agent"))

from create_pdf_project import classify
from validate_ai_proposal import validate
from create_zip_project import audit_package
from preflight_project import preflight
from generate_ai_proposal import extract_xml_candidate
from project_data import load_project, save_project

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

    def test_ai_output_extracts_only_complete_level1_fragment(self):
        raw = "Aquí tienes:\n<level1><h1>L1</h1></level1>\n"
        self.assertEqual(extract_xml_candidate(raw), "<level1><h1>L1</h1></level1>\n")
        self.assertIsNone(extract_xml_candidate("La propuesta quedó incompleta: <level1>"))

    def test_zip_audit_checks_resources_and_ignores_macos_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); package=root/'package'; package.mkdir(); (package/'images').mkdir(); (package/'__MACOSX').mkdir()
            (package/'images'/'ok.png').write_bytes(b'png')
            xml=package/'book.xml'; xml.write_text('<dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/"><book><bodymatter><level1><img src="images/ok.png"/></level1></bodymatter></book></dtbook>',encoding='utf-8')
            opf=package/'book.opf'; opf.write_text('<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/"><manifest><item href="book.xml"/><item href="images/ok.png"/></manifest></package>',encoding='utf-8')
            (package/'__MACOSX'/'._book.xml').write_bytes(b'')
            result=audit_package(root,[xml],[opf]); self.assertEqual(result['status'],'pass'); self.assertEqual(result['xml_count'],1)

    def test_preflight_blocks_missing_metadata_and_image_decisions(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'metadata').mkdir(); (root/'structure').mkdir(); (root/'inventario').mkdir()
            (root/'metadata'/'nimac.json').write_text('{"title":"Test"}',encoding='utf-8')
            (root/'structure'/'structure.json').write_text('{"units":[{"id":"u1","section":"bodymatter"}]}',encoding='utf-8')
            (root/'inventario'/'images.json').write_text('{"assets":[{"file":"x.png","status":"detected"}]}',encoding='utf-8')
            result=preflight(root); self.assertEqual(result['status'],'pending'); self.assertTrue(any(not x['ok'] for x in result['checks']))

    def test_project_structure_preserves_combined_pdf_ranges(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            structure={"units":[{"id":"L01","name":"Lesson 1","section":"bodymatter","file":"book.pdf","pages":[13,24]}]}
            save_project(root, {"title":"Book"}, structure)
            loaded=load_project(root)
            self.assertEqual(loaded["structure"]["units"][0]["pages"], [13,24])
            self.assertEqual(loaded["structure"]["units"][0]["section"], "bodymatter")

if __name__ == "__main__":
    unittest.main()
