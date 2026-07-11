import os
import sys
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from job_synthesizer import generate_job_posting, generate_job_postings, export_jobs_to_json


class TestJobSynthesizer(unittest.TestCase):
    def test_generate_single_job_has_required_keys(self):
        job = generate_job_posting(1)
        required = [
            "id", "title", "company", "location", "description",
            "key_responsibilities", "required_skills", "tech_stack",
            "experience_required", "salary_range", "employment_type",
        ]
        for key in required:
            self.assertIn(key, job, f"Missing key: {key}")

    def test_job_id_format(self):
        job = generate_job_posting(42)
        self.assertEqual(job["id"], "JOB-2026-0042")

    def test_job_has_unique_id_per_index(self):
        job1 = generate_job_posting(1)
        job2 = generate_job_posting(2)
        self.assertNotEqual(job1["id"], job2["id"])

    def test_generate_multiple_jobs(self):
        jobs = generate_job_postings(50)
        self.assertEqual(len(jobs), 50)
        ids = [j["id"] for j in jobs]
        self.assertEqual(len(set(ids)), 50)

    def test_job_title_not_empty(self):
        for i in range(20):
            job = generate_job_posting(i)
            self.assertTrue(len(job["title"]) > 0)

    def test_job_company_not_empty(self):
        job = generate_job_posting(1)
        self.assertTrue(len(job["company"]) > 0)

    def test_job_description_not_empty(self):
        job = generate_job_posting(1)
        self.assertTrue(len(job["description"]) > 50)

    def test_required_skills_has_items(self):
        job = generate_job_posting(1)
        self.assertGreater(len(job["required_skills"]), 0)

    def test_key_responsibilities_has_items(self):
        job = generate_job_posting(1)
        self.assertGreater(len(job["key_responsibilities"]), 0)

    def test_tech_stack_has_items(self):
        job = generate_job_posting(1)
        self.assertGreater(len(job["tech_stack"]), 0)

    def test_experience_required_format(self):
        job = generate_job_posting(1)
        self.assertRegex(job["experience_required"], r"\d+-\d+ years")

    def test_salary_range_format(self):
        job = generate_job_posting(1)
        self.assertIn("IDR", job["salary_range"])
        self.assertIn("-", job["salary_range"])

    def test_export_to_json(self):
        import tempfile
        jobs = generate_job_postings(10)
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "jobs.json")
        export_jobs_to_json(jobs, path)
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            loaded = json.load(f)
        self.assertEqual(len(loaded), 10)
        self.assertEqual(loaded[0]["id"], jobs[0]["id"])

    def test_job_has_source_field(self):
        job = generate_job_posting(1)
        self.assertIn("source", job)
        self.assertIn(job["source"], ["LinkedIn", "Karir.com", "Glints", "Jobstreet", "Indeed"])

    def test_job_has_work_setup(self):
        job = generate_job_posting(1)
        self.assertIn(job["work_setup"], ["On-site", "Remote", "Hybrid"])

    def test_employment_type_variety(self):
        types = set()
        for i in range(50):
            job = generate_job_posting(i)
            types.add(job["employment_type"])
        self.assertTrue(len(types) >= 1)

    def test_nice_to_have_optional(self):
        job = generate_job_posting(1)
        self.assertIn("nice_to_have", job)

    def test_100_jobs_all_unique_ids(self):
        jobs = generate_job_postings(100)
        ids = [j["id"] for j in jobs]
        self.assertEqual(len(set(ids)), 100)

    def test_100_jobs_all_have_titles(self):
        jobs = generate_job_postings(100)
        for job in jobs:
            self.assertTrue(len(job["title"]) > 0)

    def test_posting_deterministic_with_seed(self):
        import random
        random.seed(42)
        job_a = generate_job_posting(1)
        random.seed(42)
        job_b = generate_job_posting(1)
        self.assertEqual(job_a["id"], job_b["id"])


if __name__ == "__main__":
    unittest.main()
