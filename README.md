# ATS CV Generator

Generate ATS-optimized CVs in DOCX + PDF and score them against 100+ synthetic job postings to maximize your interview chances.

## Quick Start

```bash
cp data/personal_info_example.py data/personal_info.py
# Then edit data/personal_info.py with your real info

pip install -r requirements.txt
python main.py --all
```

## Commands

| Command | Description |
|---|---|
| `python main.py` | Generate CV only |
| `python main.py --all` | Full pipeline: CV → score → optimize |
| `python main.py --score` | Generate CV + ATS score report |
| `python main.py --jobs 200` | Use custom number of synthetic jobs |
| `python main.py --no-cv --score` | Score existing profile without regenerating CV |

## Output

All files go to `output/`:

- `CV_YourName.docx` — DOCX format (best for ATS)
- `CV_YourName.pdf` — PDF format
- `synthetic_jobs.json` — Generated job postings
- `ats_score_report.json` — Full scoring breakdown
- `optimization_guide.txt` — Keyword suggestions & optimization tips

## Customize

1. Copy `data/personal_info_example.py` → `data/personal_info.py`
2. Fill in your name, summary, skills, experience, projects, and education
3. Run `python main.py --all` to see your ATS score
4. Iterate: add missing keywords, improve bullet points, re-score

> `data/personal_info.py` is gitignored — your personal data stays local.

## Run Tests

```bash
python -m unittest discover tests -v
```

## How It Works

1. **CV Builder** — Converts your profile into a clean DOCX + PDF
2. **Job Synthesizer** — Generates realistic synthetic job postings biased toward your tech stack
3. **ATS Engine** — Scores your CV against each posting on keyword presence, frequency, density, section completeness, action verbs, and quantifiable achievements
4. **Optimizer** — Suggests missing keywords and provides sample bullet points

## License

MIT
