# AGENTS.md — ATS CV Generator

## Setup

```bash
cp data/personal_info_example.py data/personal_info.py  # gitignored, edit with real data
pip install -r requirements.txt
```

Create `.env` for URL key→value links (used by `cv_builder.py`):
```
MEMECHAT=https://play.google.com/store/apps/details?id=...
AOI=https://github.com/...
GUAVA_CNN=https://github.com/...
BTNMOBIILE=https://play.google.com/...
ESTETIKA=https://play.google.com/...
```

## Commands

 | Command | Action |
 |---------|--------|
 | `python main.py` | Generate CV (DOCX+PDF) |
 | `python main.py --all` | Full pipeline: generate → ATS score → optimize |
 | `python main.py --score` | Generate + score |
 | `python main.py --no-cv --score` | Score existing profile without regenerating |
 | `python main.py --jobs N` | Set synthetic job count (default 100) |
 | `python main.py --real-jobs` | Score against real crawled jobs (CV-relevant keywords) |
 | `python main.py --real-jobs --crawler-sources remoteok,dice` | Specific sources for crawling |
 | `python -m unittest discover tests -v` | Run tests |
 | `python cover_letter.py --company "Acme"` | Generate cover letter (requires llama-server at localhost:8080) |
 | `python job_crawler/crawler.py --keywords "android kotlin"` | Standalone: fetch remote jobs |
 | `python job_crawler/crawler.py --sources dice,ycjobs` | Standalone: specific sources |

## Architecture

- **`main.py`** — entrypoint. Parses args, orchestrates CV build → ATS score → optimize.
- **`cv_builder.py`** — `CVBuilder` class. Generates DOCX (python-docx) and PDF (fpdf2) from `PERSONAL_INFO` dict + `links` dict loaded from `.env`.
- **`job_synthesizer.py`** — creates synthetic job postings biased toward the target tech stack.
- **`ats_engine.py`** — `ATSScorer` + `CVOptimizer`. Weights 7 dimensions. `extract_cv_keywords()` extracts tech terms from `PERSONAL_INFO` for crawler keyword filter. `_full_text` includes `skills_sections`. Improved `_extract_keywords` with locality/biz/company filters.
- **`cover_letter.py`** — reads job posting from stdin, calls `llm_client.py` (llama.cpp server), outputs DOCX+TXT+PDF.
- **`job_crawler/`** — remote job aggregator. 14 working sources (6 free APIs + 8 scrape with playwright fallback). `Scraper` class: requests → curl_cffi → cloudscraper → playwright. Sources in `crawler.py:SOURCES` dict. Dead sources removed. `crawler_job_to_ats()` converts `Job` dataclass → ATS dict for scoring.

## Data

`data/personal_info.py` is gitignored. Schema defined in `data/personal_info_example.py`. Key dict structure:

- `portfolio`: list of `{title, description, platform, url, highlights[], doi_url?}`
- `company_projects`: list of `{title, company, platform, url, highlights[]}`
- `experience`: list of `{company, role, period, location, highlights[]}`
- `skills_sections`: list of `{title, type: "grid"|"bullets", items[]}`
- `education`, `certifications`, `languages`

The `links` dict (from `.env`) maps URL keys (e.g., `MEMECHAT`) to real URLs. Portfolio/project items reference these by key.

## Conventions

- Underline: only under text glyphs, not whitespace. For inline platform links (`(Play Store)`), render leading space as separate cell without underline.
- Dashes: use regular hyphen `-` everywhere. No en dash `–`, em dash `—`, or bullet `•` in contact separators — use `-` instead.
- DOI references: append to first portfolio highlight sentence as text. If item has `doi_url`, make the entire first bullet clickable via `link=doi_url` in PDF `multi_cell` and `_add_hyperlink` in DOCX.
- PDF: fpdf2. Use `set_draw_color` before `pdf.line`, set font before `get_string_width`.
- DOCX: python-docx. Use `_add_hyperlink(paragraph, text, url, font_size=N)` for clickable links.
- Output: all files go to `output/` (gitignored via `output/` in `.gitignore`).

## Testing

```bash
python -m unittest discover tests -v
```

Tests use `unittest`. Synthetic jobs are generated deterministically — output files in `output/` are not committed.
