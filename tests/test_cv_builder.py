import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cv_builder import CVBuilder
from data.personal_info import PERSONAL_INFO


class TestCVBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = CVBuilder(PERSONAL_INFO)
        self.temp_dir = tempfile.mkdtemp()

    def test_build_docx_creates_file(self):
        path = os.path.join(self.temp_dir, "test.docx")
        result = self.builder.build_docx(path)
        self.assertTrue(os.path.exists(result))
        self.assertGreater(os.path.getsize(result), 1000)

    def test_build_pdf_creates_file(self):
        path = os.path.join(self.temp_dir, "test.pdf")
        result = self.builder.build_pdf(path)
        self.assertTrue(os.path.exists(result))
        self.assertGreater(os.path.getsize(result), 1000)

    def test_both_formats_different_paths(self):
        docx_path = os.path.join(self.temp_dir, "cv.docx")
        pdf_path = os.path.join(self.temp_dir, "cv.pdf")
        self.builder.build_docx(docx_path)
        self.builder.build_pdf(pdf_path)
        self.assertTrue(os.path.exists(docx_path))
        self.assertTrue(os.path.exists(pdf_path))

    def test_build_docx_with_empty_skills(self):
        info = dict(PERSONAL_INFO)
        info["skills"] = []
        builder = CVBuilder(info)
        path = os.path.join(self.temp_dir, "empty_skills.docx")
        result = builder.build_docx(path)
        self.assertTrue(os.path.exists(result))

    def test_build_docx_with_no_experience(self):
        info = dict(PERSONAL_INFO)
        info["experience"] = []
        builder = CVBuilder(info)
        path = os.path.join(self.temp_dir, "no_exp.docx")
        result = builder.build_docx(path)
        self.assertTrue(os.path.exists(result))

    def test_build_pdf_with_minimal_info(self):
        info = dict(PERSONAL_INFO)
        info["summary"] = "Test summary"
        info["skills"] = ["Kotlin"]
        info["experience"] = []
        info["education"] = []
        info["certifications"] = []
        builder = CVBuilder(info)
        path = os.path.join(self.temp_dir, "minimal.pdf")
        result = builder.build_pdf(path)
        self.assertTrue(os.path.exists(result))

    def test_keyword_density_returns_dict(self):
        density = self.builder.get_keyword_density()
        self.assertIsInstance(density, dict)
        self.assertGreater(len(density), 0)
        # Should have at least some keywords present
        total = sum(density.values())
        self.assertGreater(total, 10)

    def test_ats_keywords_defined(self):
        keywords = CVBuilder.ATS_KEYWORDS
        self.assertGreater(len(keywords), 15)
        self.assertIn("Kotlin", keywords)
        self.assertIn("Clean Architecture", keywords)
        self.assertIn("Jetpack Compose", keywords)

    def test_personal_info_has_all_sections(self):
        required = ["name", "title", "summary", "skills", "experience", "education"]
        for section in required:
            self.assertIn(section, PERSONAL_INFO, f"Missing section: {section}")

    def test_personal_info_experience_has_highlights(self):
        for exp in PERSONAL_INFO["experience"]:
            self.assertIn("company", exp)
            self.assertIn("role", exp)
            self.assertIn("highlights", exp)
            self.assertGreater(len(exp["highlights"]), 0)

    def test_experience_highlights_quantified(self):
        import re
        total = 0
        with_numbers = 0
        for exp in PERSONAL_INFO["experience"]:
            for h in exp["highlights"]:
                total += 1
                if re.search(r"\d+", h):
                    with_numbers += 1
        ratio = with_numbers / total if total > 0 else 0
        self.assertGreaterEqual(
            ratio, 0.3,
            f"Only {with_numbers}/{total} highlights have quantifiable metrics"
        )


if __name__ == "__main__":
    unittest.main()
