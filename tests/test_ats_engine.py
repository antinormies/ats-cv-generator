import os
import sys
import json
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ats_engine import ATSScorer, CVOptimizer
from cv_builder import CVBuilder
from data.personal_info import PERSONAL_INFO
from job_synthesizer import generate_job_posting


class TestATSScorer(unittest.TestCase):
    def setUp(self):
        self.builder = CVBuilder(PERSONAL_INFO)
        self.scorer = ATSScorer(self.builder)
        self.sample_job = generate_job_posting(1)

    def test_score_keyword_presence_finds_matches(self):
        keywords = ["Kotlin", "Android", "Clean Architecture"]
        score, found, missing = self.scorer.score_keyword_presence(keywords)
        self.assertGreater(score, 0)
        self.assertIn("Kotlin", found)
        self.assertEqual(len(missing) + len(found), len(keywords))

    def test_score_keyword_presence_all_missing(self):
        keywords = ["NonExistentTechXYZ", "FakeFrameworkABC"]
        score, found, missing = self.scorer.score_keyword_presence(keywords)
        self.assertEqual(score, 0)
        self.assertEqual(len(found), 0)
        self.assertEqual(len(missing), 2)

    def test_score_keyword_presence_empty_list(self):
        score, found, missing = self.scorer.score_keyword_presence([])
        self.assertEqual(score, 0)

    def test_score_keyword_frequency(self):
        keywords = ["Kotlin", "Android", "Firebase"]
        score, freq = self.scorer.score_keyword_frequency(keywords)
        self.assertGreaterEqual(score, 0)
        self.assertIsInstance(freq, dict)

    def test_score_keyword_density(self):
        keywords = ["Kotlin", "Android", "Java", "Clean Architecture", "Firebase"]
        score = self.scorer.score_keyword_density(keywords)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, self.scorer.WEIGHTS["keyword_density"])

    def test_score_section_completeness(self):
        score = self.scorer.score_section_completeness()
        self.assertGreater(score, 0)
        self.assertLessEqual(score, self.scorer.WEIGHTS["section_completeness"])

    def test_score_formatting(self):
        score = self.scorer.score_formatting()
        self.assertGreater(score, 0)
        self.assertLessEqual(score, self.scorer.WEIGHTS["formatting"])

    def test_score_action_verbs(self):
        score, verbs = self.scorer.score_action_verbs()
        self.assertGreater(score, 0)
        self.assertGreater(len(verbs), 0)

    def test_score_quantifiable_achievements(self):
        score, found = self.scorer.score_quantifiable_achievements()
        self.assertGreater(score, 0)
        self.assertGreater(len(found), 0)

    def test_score_for_job_returns_valid_structure(self):
        result = self.scorer.score_for_job(self.sample_job)
        self.assertIn("total_score", result)
        self.assertIn("breakdown", result)
        self.assertIn("details", result)
        self.assertIn("matched_keywords", result["details"])
        self.assertIn("missing_keywords", result["details"])
        self.assertIn("job_title", result)
        self.assertIn("company", result)

    def test_score_for_job_score_range(self):
        result = self.scorer.score_for_job(self.sample_job)
        self.assertGreaterEqual(result["total_score"], 0)
        self.assertLessEqual(result["total_score"], result["max_score"])

    def test_breakdown_sum_matches_total(self):
        result = self.scorer.score_for_job(self.sample_job)
        breakdown_sum = sum(v["score"] for v in result["breakdown"].values())
        self.assertAlmostEqual(result["total_score"], breakdown_sum, delta=0.5)

    def test_comprehensive_score_multiple_jobs(self):
        jobs = [generate_job_posting(i) for i in range(10)]
        result = self.scorer.comprehensive_score(jobs)
        self.assertIn("average_ats_score", result)
        self.assertIn("score_distribution", result)
        self.assertIn("globally_matched_keywords", result)
        self.assertIn("globally_missing_keywords", result)
        self.assertIn("suggestions", result)
        self.assertEqual(result["jobs_scored"], 10)
        self.assertGreaterEqual(result["average_ats_score"], 0)

    def test_comprehensive_score_empty_jobs(self):
        result = self.scorer.comprehensive_score([])
        self.assertIn("error", result)

    def test_comprehensive_score_distribution_counts(self):
        jobs = [generate_job_posting(i) for i in range(50)]
        result = self.scorer.comprehensive_score(jobs)
        dist = result["score_distribution"]
        total = sum(dist.values())
        self.assertEqual(total, result["jobs_scored"])

    def test_extract_keywords_captures_tech_terms(self):
        text = "Experience with Kotlin and Jetpack Compose and Clean Architecture"
        keywords = self.scorer._extract_keywords(text)
        self.assertIn("Kotlin", keywords)
        self.assertIn("Jetpack Compose", keywords)
        self.assertIn("Clean Architecture", keywords)

    def test_action_verbs_list_defined(self):
        self.assertGreater(len(ATSScorer.ACTION_VERBS), 20)

    def test_weights_sum_to_100(self):
        total = sum(ATSScorer.WEIGHTS.values())
        self.assertEqual(total, 100)

    def test_quantifiable_patterns_match(self):
        import re
        text = "reduced by 40% improved 50K users handled 1000+ transactions"
        matches = []
        for pat in ATSScorer.QUANTIFIABLE_PATTERNS:
            matches.extend(re.findall(pat, text))
        self.assertGreater(len(matches), 0)

    def test_score_preserves_different_jobs(self):
        job1 = generate_job_posting(1)
        job2 = generate_job_posting(2)
        score1 = self.scorer.score_for_job(job1)
        score2 = self.scorer.score_for_job(job2)
        self.assertIsInstance(score1["total_score"], (int, float))
        self.assertIsInstance(score2["total_score"], (int, float))


class TestCVOptimizer(unittest.TestCase):
    def setUp(self):
        self.builder = CVBuilder(PERSONAL_INFO)
        self.optimizer = CVOptimizer(self.builder)

    def test_suggest_keywords_returns_list(self):
        jobs = [generate_job_posting(i) for i in range(20)]
        suggestions = self.optimizer.suggest_keywords_from_jobs(jobs, top_n=10)
        self.assertGreater(len(suggestions), 0)
        self.assertLessEqual(len(suggestions), 10)

    def test_suggest_keywords_from_empty_jobs(self):
        suggestions = self.optimizer.suggest_keywords_from_jobs([], top_n=5)
        self.assertEqual(len(suggestions), 0)

    def test_generate_optimized_cv_creates_file(self):
        import tempfile
        jobs = [generate_job_posting(i) for i in range(10)]
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "guide.txt")
        result = self.optimizer.generate_optimized_cv(jobs, path)
        self.assertTrue(os.path.exists(result))
        self.assertGreater(os.path.getsize(result), 100)


if __name__ == "__main__":
    unittest.main()
