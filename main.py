#!/usr/bin/env python3
"""
ATS-Optimized CV Generator for Android Developers

Generates CV in DOCX and PDF formats with ATS scoring against
synthetic job postings. Provides optimization suggestions.

Usage:
    python main.py              # Generate CV with default profile
    python main.py --score      # Generate CV + ATS score report
    python main.py --jobs N     # Generate N synthetic jobs (default 100)
    python main.py --all        # Full pipeline: generate, score, optimize
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cv_builder import CVBuilder
from ats_engine import ATSScorer, CVOptimizer
from job_synthesizer import generate_job_postings, export_jobs_to_json
from job_crawler.crawler import SOURCES, Scraper, deduplicate, crawler_job_to_ats, write_jobs_excel
from ats_engine import ATSScorer, CVOptimizer, extract_cv_keywords

try:
    from data.personal_info import PERSONAL_INFO
except ImportError:
    print("=" * 60)
    print("  ERROR: data/personal_info.py not found.")
    print("=" * 60)
    print()
    print("  Copy the example file and customize it:")
    print()
    print("    cp data/personal_info_example.py data/personal_info.py")
    print()
    print("  Then edit data/personal_info.py with your information.")
    print()
    sys.exit(1)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_env_links():
    links = {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    links[k.strip()] = v.strip()
    return links


def generate_cv(formats=None):
    ensure_output_dir()
    links = load_env_links()
    builder = CVBuilder(PERSONAL_INFO, links)
    results = {}
    if formats is None:
        formats = ["docx", "pdf"]
    if "docx" in formats:
        path = os.path.join(OUTPUT_DIR, "CV_DaniZakaria.docx")
        results["docx"] = builder.build_docx(path)
        print(f"✅ DOCX generated: {results['docx']}")
    if "pdf" in formats:
        path = os.path.join(OUTPUT_DIR, "CV_DaniZakaria.pdf")
        results["pdf"] = builder.build_pdf(path)
        print(f"✅ PDF generated: {results['pdf']}")
    return builder, results


def score_cv(builder, jobs):
    print(f"\n{'='*60}")
    print("ATS SCORING REPORT")
    print(f"{'='*60}")
    scorer = ATSScorer(builder)
    result = scorer.comprehensive_score(jobs)
    print(f"\n📊 Average ATS Score: {result['average_ats_score']}/{result['max_score']}")
    print(f"📈 Jobs scored: {result['jobs_scored']}")
    print(f"\nScore Distribution:")
    for bucket, count in result["score_distribution"].items():
        bar = "█" * count + "░" * (20 - count) if count <= 20 else "█" * 20
        print(f"  {bucket}: {count:3d} jobs {bar}")
    print(f"\n🔑 Missing Top Keywords:")
    if result["globally_missing_keywords"]:
        for kw in result["globally_missing_keywords"][:15]:
            print(f"  ✗ {kw}")
    else:
        print("  None! Your CV covers all common keywords.")
    print(f"\n💡 Suggestions:")
    for s in result["suggestions"]:
        print(f"  → {s}")
    result_path = os.path.join(OUTPUT_DIR, "ats_score_report.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n📄 Full report saved to: {result_path}")
    return result


def optimize_cv(builder, jobs):
    ensure_output_dir()
    optimizer = CVOptimizer(builder)
    path = os.path.join(OUTPUT_DIR, "optimization_guide.txt")
    optimizer.generate_optimized_cv(jobs, path)
    print(f"📄 Optimization guide saved to: {path}")
    return path


def generate_jobs(count=100):
    ensure_output_dir()
    jobs = generate_job_postings(count)
    path = os.path.join(OUTPUT_DIR, "synthetic_jobs.json")
    export_jobs_to_json(jobs, path)
    print(f"✅ Generated {len(jobs)} synthetic job postings → {path}")
    return jobs


def main():
    parser = argparse.ArgumentParser(
        description="ATS-Optimized CV Generator for Android Developers"
    )
    parser.add_argument("--score", action="store_true", help="Run ATS scoring against synthetic jobs")
    parser.add_argument("--jobs", type=int, default=100, help="Number of synthetic jobs to generate")
    parser.add_argument("--all", action="store_true", help="Run full pipeline (generate + score + optimize)")
    parser.add_argument("--no-cv", action="store_true", help="Skip CV generation")
    parser.add_argument("--real-jobs", action="store_true", help="Score against real crawled jobs (CV-relevant keywords)")
    parser.add_argument("--crawler-sources", default="all", help="Crawler sources for --real-jobs")
    parser.add_argument("--excel", action="store_true", help="Export crawled jobs to XLSX")
    args = parser.parse_args()

    print(f"{'='*60}")
    print("  ATS-OPTIMIZED CV GENERATOR")
    print(f"  Target: Senior Android Mobile Developer")
    print(f"{'='*60}\n")

    if args.all:
        args.score = True

    if not args.no_cv:
        builder, paths = generate_cv()
    else:
        builder = CVBuilder(PERSONAL_INFO, load_env_links())

    if args.real_jobs:
        cv_keywords = extract_cv_keywords(PERSONAL_INFO)
        print(f"  CV-extracted keywords: {cv_keywords[:120]}...")
        print()
        s = Scraper()
        all_jobs = []
        selected = list(SOURCES.keys()) if args.crawler_sources == "all" else [x.strip() for x in args.crawler_sources.split(",") if x.strip()]
        for name in selected:
            print(f"  Crawling {name}...")
            try:
                jobs = SOURCES[name](s, keywords=cv_keywords)
                all_jobs.extend(jobs)
                print(f"    → {len(jobs)} jobs")
            except Exception as e:
                print(f"    → ERROR: {e}")
        all_jobs = deduplicate(all_jobs)
        jobs = [crawler_job_to_ats(j) for j in all_jobs]
        print(f"  Total unique jobs: {len(jobs)}")
        job_path = os.path.join(OUTPUT_DIR, "crawled_jobs.json")
        with open(job_path, "w") as f:
            json.dump(jobs, f, indent=2)
        print(f"  JSON saved to {job_path}")
        if args.excel:
            xlsx_path = os.path.join(OUTPUT_DIR, "crawled_jobs.xlsx")
            write_jobs_excel(all_jobs, xlsx_path)
            print(f"  Excel saved to {xlsx_path}")
    else:
        jobs = generate_jobs(args.jobs)

    if args.score or args.all:
        score_cv(builder, jobs)
        optimize_cv(builder, jobs)

    print(f"\n{'='*60}")
    print("  DONE! Check the 'output/' folder for all files.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
