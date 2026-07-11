#!/usr/bin/env python3
"""
Cover Letter Generator

Generates a tailored cover letter in DOCX + TXT + PDF formats using a local
llama.cpp LLM server and your CV profile.

Usage (pipe):
    cat job.txt | python cover_letter.py --company "Acme Corp"

Usage (interactive):
    python cover_letter.py --company "Acme Corp"
    Paste job posting, then press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows)

Usage (with recipient):
    cat job.txt | python cover_letter.py --company "Acme Corp" --recipient "John"
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


def read_job_posting() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    print("Paste the job posting below, then press Ctrl+D when done:")
    print("-" * 40)
    lines = []
    try:
        for line in sys.stdin:
            lines.append(line)
    except KeyboardInterrupt:
        print()
        sys.exit(1)
    return "".join(lines).strip()


def save_txt(path: str, body: str, company: str, recipient: str):
    from datetime import date
    lines = []
    lines.append(f"Date: {date.today().strftime('%B %d, %Y')}")
    if company:
        lines.append(f"Company: {company}")
    lines.append("")
    lines.append(f"Re: Application for {PERSONAL_INFO['title']} Position")
    lines.append("")
    lines.append("Dear Hiring Manager,")
    lines.append("")
    lines.append(body)
    lines.append("")
    lines.append("Best regards,")
    lines.append(PERSONAL_INFO["name"])
    lines.append("")
    if PERSONAL_INFO.get("phone"):
        lines.append(PERSONAL_INFO["phone"])
    if PERSONAL_INFO.get("email"):
        lines.append(PERSONAL_INFO["email"])
    with open(path, "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Generate a tailored cover letter")
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

    job_text = read_job_posting()
    if not job_text:
        print("Error: no job posting provided")
        sys.exit(1)

    print(f"📝 Generating cover letter...")
    print(f"   Job posting: {len(job_text)} chars")
    print(f"   Company: {args.company or '(not specified)'}")
    print()

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

    print("   Cover letter generated successfully.")
    print()

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    company_slug = args.company.replace(" ", "_") if args.company else "Unknown"
    base = os.path.join(output_dir, f"CoverLetter_{company_slug}")

    docx_path = base + ".docx"
    txt_path = base + ".txt"
    pdf_path = base + ".pdf"

    builder = CoverLetterBuilder(PERSONAL_INFO)
    builder.build(docx_path, body=body, company=args.company, recipient=args.recipient)
    save_txt(txt_path, body, args.company, args.recipient)
    builder.build_pdf(pdf_path, body=body, company=args.company, recipient=args.recipient)

    print(f"✅ DOCX: {docx_path}")
    print(f"✅ TXT:  {txt_path}")
    print(f"✅ PDF:  {pdf_path}")
    print()
    print("--- Preview ---")
    for line in body.split("\n")[:8]:
        if line.strip():
            print(f"  {line.strip()}")
    if body.count("\n") > 8:
        print("  ...")
    print("---------------")


if __name__ == "__main__":
    main()
