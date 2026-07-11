#!/usr/bin/env python3
"""
Cover Letter Generator

Generates a tailored cover letter in DOCX format using a local llama.cpp
LLM server and your CV profile.

Usage:
    python cover_letter.py --job-posting job.txt
    python cover_letter.py --job-posting job.txt --company "Acme Corp" --recipient "Hiring Manager"
    python cover_letter.py --job-posting job.txt --output my_letter.docx
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    sys.exit(1)

from cover_letter_builder import CoverLetterBuilder
from llm_client import generate_cover_letter, list_models


def main():
    parser = argparse.ArgumentParser(description="Generate a tailored cover letter")
    parser.add_argument(
        "--job-posting", "-j",
        required=True,
        help="Path to a text file containing the job posting",
    )
    parser.add_argument(
        "--company", "-c",
        default="",
        help="Company name to address the letter to",
    )
    parser.add_argument(
        "--recipient", "-r",
        default="",
        help="Recipient name (e.g. Hiring Manager name)",
    )
    parser.add_argument(
        "--output", "-o",
        default="",
        help="Output DOCX path (default: output/CoverLetter_[Company].docx)",
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help="Model name on llama-server (auto-detected if omitted)",
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.6,
        help="LLM temperature (default: 0.6)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2000,
        help="Max tokens for LLM response (default: 2000)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.job_posting):
        print(f"Error: job posting file not found: {args.job_posting}")
        sys.exit(1)

    with open(args.job_posting) as f:
        job_text = f.read().strip()

    if not job_text:
        print("Error: job posting file is empty")
        sys.exit(1)

    print("📝 Generating cover letter...")
    print(f"   Job posting: {args.job_posting} ({len(job_text)} chars)")
    print(f"   Company: {args.company or '(not specified)'}")
    print()

    # Check LLM connectivity
    print("🔌 Checking llama-server...")
    try:
        models = list_models()
        model = args.model or models[0]
        print(f"   Connected. Using model: {model}")
    except ConnectionError as e:
        print(f"   Error: {e}")
        print()
        print("   Make sure llama-server is running:")
        print("     http://localhost:8080")
        sys.exit(1)

    # Generate body
    print("🤖 Generating cover letter content...")
    try:
        body = generate_cover_letter(
            job_posting=job_text,
            cv_summary=PERSONAL_INFO["summary"],
            cv_skills=PERSONAL_INFO["skills"],
            cv_experience=PERSONAL_INFO["experience"],
            model=model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    except RuntimeError as e:
        print(f"   Error: {e}")
        sys.exit(1)

    print("   Cover letter body generated successfully.")
    print()

    # Build DOCX
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    if args.output:
        output_path = args.output
    else:
        company_slug = args.company.replace(" ", "_") if args.company else "Unknown"
        output_path = os.path.join(output_dir, f"CoverLetter_{company_slug}.docx")

    builder = CoverLetterBuilder(PERSONAL_INFO)
    builder.build(output_path, body=body, company=args.company, recipient=args.recipient)

    print(f"✅ Cover letter saved: {output_path}")
    print()
    print("--- Preview ---")
    print(body[:500] + ("..." if len(body) > 500 else ""))
    print("---------------")


if __name__ == "__main__":
    main()
