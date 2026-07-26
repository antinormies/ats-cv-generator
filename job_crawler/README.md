# Job Crawler — Remote Job Aggregator

Aggregates remote job listings from 14 working sources with multi-strategy anti-bot bypass. Built for the ATS CV pipeline.

## Working Sources

### Free APIs (no key)
| Board | Source | Notes |
|-------|--------|-------|
| **RemoteOK** | `remoteok` | JSON feed, up to 100 jobs |
| **Remotive** | `remotive` | ~1000+ live, categorized |
| **Arbeitnow** | `arbeitnow` | EU+global remote |
| **Himalayas** | `himalayas` | Remote-first, culture tags |
| **Jobicy** | `jobicy` | Remote + hybrid |
| **4 Day Week** | `4dayweek` | 4-day work week filter |

### Scrape-based (server-rendered)
| Board | Source | Notes |
|-------|--------|-------|
| **We Work Remotely** | `weworkremotely` | 247+ jobs across categories |
| **Built In** | `builtin` | 20-30 jobs per query |
| **JustRemote** | `justremote` | ~11 jobs |
| **Dice** | `dice` | 34+ jobs, playwright fallback |
| **YC Jobs** | `ycjobs` | 27+ jobs, playwright fallback |
| **Web3.Career** | `web3.career` | 48+ crypto/web3 jobs |
| **CryptoJobsList** | `cryptojobslist` | 1-5 jobs |
| **CryptoJobs** | `crypto.jobs` | ~12 jobs |

### Dead/Blocked Sources
Wellfound (DataDome), StackOverflow (403), Working Nomads (unresponsive), Pangian (404), Hired (rebranded to LHH), HNHiring (dead).

## Architecture

```
job_crawler/
├── crawler.py   # Main entry: 17 scrape functions, Scraper class, dedup, CLI
├── site_sources.txt  # 50+ source catalog with bypass recipes
└── requirements.txt
```

All 14 source modules live in `crawler.py` as standalone `scrape_*` functions. The `Scraper` class provides layered bypass:
1. `requests` (no-bot sites)
2. `curl_cffi` (TLS impersonation)
3. `cloudscraper` (JS challenge solving)
4. `playwright` (full Chromium for SPA/Turnstile)

## Usage

```bash
cd job_crawler
pip install -r requirements.txt
playwright install chromium  # first time only

# All sources
python crawler.py --keywords "android kotlin"

# Specific sources
python crawler.py --keywords "rust" --sources remoteok,remotive,arbeitnow

# No keyword filter (everything)
python crawler.py --keywords ""

# Output to JSON
python crawler.py --output /tmp/jobs.json
```

Typical output: 600-800+ deduplicated jobs across all sources (~30-60s runtime).
