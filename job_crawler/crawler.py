"""
Remote job aggregator — multi-source, multi-bypass.
Scrapes 50+ job boards for remote/IT/web3 roles.
"""

import argparse
import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ua = UserAgent()

# ---------------------------------------------------------------------------
# Normalized schema
# ---------------------------------------------------------------------------

@dataclass
class Job:
    title: str
    company: str
    location: str = ""
    url: str = ""
    source: str = ""
    description: str = ""
    salary: str = ""
    tags: list[str] = field(default_factory=list)
    remote: bool = True
    posted_at: str = ""


# ---------------------------------------------------------------------------
# Scraping engine with layered bypass
# ---------------------------------------------------------------------------

class Scraper:
    """Multi-backend scraper: requests -> curl_cffi -> cloudscraper -> playwright."""

    def __init__(self, proxy: str = "", captcha_key: str = ""):
        self.proxy = proxy
        self.captcha_key = captcha_key
        self._session = requests.Session()
        self._session.headers.update({"Accept-Language": "en-US,en;q=0.9"})
        self._cloudscraper = None
        self._curl = None

    def _get_cloudscraper(self):
        if self._cloudscraper is None:
            import cloudscraper
            kwargs = {"interpreter": "native"}
            if self.proxy:
                kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}
            self._cloudscraper = cloudscraper.create_scraper(**kwargs)
        return self._cloudscraper

    def _get_curl(self):
        if self._curl is None:
            from curl_cffi import requests as curl_req
            self._curl = curl_req
        return self._curl

    @staticmethod
    def _has_real_content(html: str) -> bool:
        if len(html) < 1000:
            return False
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator=" ", strip=True)
        return len(text) > 200

    def get(self, url: str, timeout: int = 30) -> str:
        headers = {"User-Agent": ua.random}
        # Strategy 1: standard requests (works for no-bot sites)
        try:
            resp = self._session.get(url, headers=headers, timeout=timeout, proxies=self._proxy_dict())
            if resp.status_code == 200 and "cf-browser-verification" not in resp.text[:2000] and self._has_real_content(resp.text):
                return resp.text
        except Exception:
            pass

        # Strategy 2: curl_cffi (TLS impersonation)
        try:
            curl = self._get_curl()
            resp = curl.get(url, impersonate="chrome", timeout=timeout, proxies=self._proxy_dict())
            if resp.status_code == 200 and self._has_real_content(resp.text):
                return resp.text
        except Exception:
            pass

        # Strategy 3: cloudscraper (JS challenge solving)
        try:
            sc = self._get_cloudscraper()
            resp = sc.get(url, timeout=timeout)
            if resp.status_code == 200 and self._has_real_content(resp.text):
                return resp.text
        except Exception as e:
            log.warning(f"cloudscraper failed for {url}: {e}")

        # Strategy 4: playwright (full browser) — for SPA / Turnstile / hCaptcha
        try:
            return self._playwright_get(url, timeout)
        except Exception as e:
            log.warning(f"playwright failed for {url}: {e}")

        raise RuntimeError(f"All bypass strategies failed for {url}")

    def _proxy_dict(self):
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return {}

    def _playwright_get(self, url: str, timeout: int) -> str:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            ctx = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=ua.random,
            )
            page = ctx.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            html = page.content()
            browser.close()
            return html

    def get_json(self, url: str, timeout: int = 30) -> dict | list:
        headers = {"User-Agent": ua.random}
        try:
            resp = self._session.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        try:
            curl = self._get_curl()
            resp = curl.get(url, impersonate="chrome", timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        raise RuntimeError(f"JSON fetch failed for {url}")


# ---------------------------------------------------------------------------
# Source: RemoteOK (API)
# ---------------------------------------------------------------------------

def scrape_remoteok(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        data = s.get_json("https://remoteok.com/api")
        raw = []
        if isinstance(data, list):
            raw = data
        elif isinstance(data, dict):
            raw = data.get("jobs", [])
        for j in raw:
            if not isinstance(j, dict) or ("position" not in j and "title" not in j):
                continue
            title = j.get("position") or j.get("title", "")
            company = j.get("company", "")
            text_for_kw = title + " " + company + " " + " ".join(j.get("tags", []))
            if keywords and not _match_keywords(text_for_kw, keywords):
                continue
            url = j.get("apply_url") or j.get("url", "")
            jobs.append(Job(
                title=title,
                company=company,
                location=j.get("location", "Remote"),
                url=url,
                source="remoteok",
                description=j.get("description", ""),
                salary=f"{j.get('salary_min', '')} - {j.get('salary_max', '')}",
                tags=[t.strip() for t in j.get("tags", [])],
                remote=True,
            ))
    except Exception as e:
        log.warning(f"remoteok: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Remotive (API)
# ---------------------------------------------------------------------------

def scrape_remotive(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    for cat in ("software-dev", "dev", "product", "customer-support", "marketing"):
        try:
            data = s.get_json(f"https://remotive.com/api/remote-jobs?category={cat}&limit=100")
            for j in data.get("jobs", []):
                if keywords and not _match_keywords(j.get("title", "") + " " + j.get("description", ""), keywords):
                    continue
                jobs.append(Job(
                    title=j.get("title", ""),
                    company=j.get("company_name", ""),
                    location=j.get("candidate_required_location", "Remote"),
                    url=j.get("url", ""),
                    source="remotive",
                    description=j.get("description", ""),
                    salary=j.get("salary", ""),
                    tags=[t.strip() for t in j.get("tags", [])],
                    remote=True,
                ))
        except Exception as e:
            log.warning(f"remotive/{cat}: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Arbeitnow (API)
# ---------------------------------------------------------------------------

def scrape_arbeitnow(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        data = s.get_json("https://arbeitnow.com/api/job-board-api")
        for j in data.get("data", []):
            if keywords and not _match_keywords(j.get("title", "") + " " + j.get("description", ""), keywords):
                continue
            jobs.append(Job(
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                location=j.get("location", "Remote"),
                url=j.get("url", ""),
                source="arbeitnow",
                description=j.get("description", ""),
                salary=j.get("salary", ""),
                tags=[t.strip() for t in j.get("tags", [])],
                remote=j.get("remote", False),
            ))
    except Exception as e:
        log.warning(f"arbeitnow: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Himalayas (API)
# ---------------------------------------------------------------------------

def scrape_himalayas(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        data = s.get_json("https://himalayas.app/jobs/api")
        raw = data.get("jobs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not isinstance(raw, list):
            raw = []
        for j in raw:
            title = j.get("title", "")
            company = j.get("companyName", "") or j.get("company", "")
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            url = j.get("url", "") or j.get("applyUrl", "") or ""
            jobs.append(Job(
                title=title,
                company=company,
                location="Remote",
                url=url,
                source="himalayas",
                description=j.get("excerpt", "") or j.get("description", ""),
                tags=j.get("skills", []) or j.get("tags", []),
                remote=True,
            ))
    except Exception as e:
        log.warning(f"himalayas: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Jobicy (API)
# ---------------------------------------------------------------------------

def scrape_jobicy(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        data = s.get_json("https://jobicy.com/api/v2/remote-jobs")
        for j in data.get("jobs", []):
            if keywords and not _match_keywords(j.get("jobTitle", "") + " " + j.get("jobDescription", ""), keywords):
                continue
            jobs.append(Job(
                title=j.get("jobTitle", ""),
                company=j.get("companyName", ""),
                location=j.get("jobGeoLocation", "Remote"),
                url=j.get("url", ""),
                source="jobicy",
                description=j.get("jobDescription", ""),
                salary=j.get("annualSalaryMin", "") or "",
                remote=True,
            ))
    except Exception as e:
        log.warning(f"jobicy: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: 4 Day Week (API)
# ---------------------------------------------------------------------------

def scrape_4dayweek(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        data = s.get_json("https://4dayweek.io/api/jobs")
        raw = data.get("jobs", []) if isinstance(data, dict) else []
        for j in raw:
            title = j.get("title", "")
            company = j.get("company_name", "")
            if keywords and not _match_keywords(title + " " + company + " " + " ".join(j.get("tags", [])), keywords):
                continue
            locs = j.get("locations", [])
            loc = locs[0].get("city", "") if locs and isinstance(locs[0], dict) else (locs[0] if locs else "Remote")
            slug = j.get("slug", "")
            url = f"https://4dayweek.io/job/{slug}" if slug else ""
            tags = j.get("tags", []) if isinstance(j.get("tags"), list) else []
            salary = j.get("salary_label", "") or j.get("salary", "")
            jobs.append(Job(
                title=title,
                company=company,
                location=loc,
                url=url,
                source="4dayweek",
                salary=salary,
                tags=tags,
                remote=j.get("work_arrangement", "") == "remote",
            ))
    except Exception as e:
        log.warning(f"4dayweek: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: We Work Remotely (scrape)
# ---------------------------------------------------------------------------

def scrape_weworkremotely(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    for cat in ("", "category/remote-full-stack-programming-jobs", "category/remote-front-end-programming-jobs",
                "category/remote-back-end-programming-jobs", "category/remote-devops-sysadmin-jobs"):
        try:
            url = f"https://weworkremotely.com/{cat}" if cat else "https://weworkremotely.com/"
            html = s.get(url)
            soup = BeautifulSoup(html, "lxml")
            for a in soup.select("a[href*='/remote-jobs/']"):
                href = a.get("href", "")
                if not href.startswith("/remote-jobs/"):
                    continue
                title_el = a.select_one("span.title") or a
                company_el = a.select_one("span.company") or a.select_one(".company-name")
                title = title_el.text.strip() if title_el != a else a.get("title", "") or a.text.strip()
                company = company_el.text.strip()[:60] if company_el else ""
                text_for_kw = title + " " + company
                if keywords and not _match_keywords(text_for_kw, keywords):
                    continue
                url_full = f"https://weworkremotely.com{href}" if href.startswith("/") else href
                loc_el = a.select_one("span.region") or a.select_one(".location")
                desc_el = a.select_one("span.description")
                tag_el = a.select_one("span.badge") or a.select_one(".tag")
                jobs.append(Job(
                    title=title, company=company,
                    location=loc_el.text.strip() if loc_el else "Remote",
                    url=url_full, source="weworkremotely",
                    description=desc_el.text.strip() if desc_el else "",
                    tags=[tag_el.text.strip()] if tag_el else [],
                    remote=True,
                ))
        except Exception as e:
            log.warning(f"weworkremotely/{cat}: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Remote.co (scrape)
# ---------------------------------------------------------------------------

def scrape_remoteco(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://remote.co/remote-jobs/")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select(".job-list-card"):
            title_el = card.select_one("h3 a")
            company_el = card.select_one("h4[id*='-company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://remote.co{href}"
            loc_el = card.select_one("[class*='location']") or card.select_one(".sc-kSTGyJ")
            loc = loc_el.text.strip() if loc_el else "Remote"
            jobs.append(Job(
                title=title, company=company, location=loc,
                url=url, source="remote.co",
                remote="remote" in loc.lower() or "hybrid" in loc.lower(),
            ))
    except Exception as e:
        log.warning(f"remote.co: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Working Nomads (scrape)
# ---------------------------------------------------------------------------

def scrape_workingnomads(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://www.workingnomads.com/jobs")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select(".job-card") or soup.select(".job-listing") or soup.select("article"):
            title_el = card.select_one("h2 a") or card.select_one("a")
            company_el = card.select_one(".company") or card.select_one(".company-name")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://www.workingnomads.com{href}"
            desc_el = card.select_one("p")
            jobs.append(Job(
                title=title, company=company, location="Remote",
                url=url, source="workingnomads",
                description=desc_el.text.strip() if desc_el else "",
                remote=True,
            ))
    except Exception as e:
        log.warning(f"workingnomads: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Web3.Career (scrape)
# ---------------------------------------------------------------------------

def scrape_web3career(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    for url_path in ("remote-jobs", "backend-jobs", "solidity-jobs", "full-time"):
        try:
            html = s.get(f"https://web3.career/{url_path}")
            soup = BeautifulSoup(html, "lxml")
            for tr in soup.select("table tbody tr") or soup.select(".job-row") or soup.select("[class*='job']"):
                cells = tr.select("td")
                if len(cells) < 3:
                    continue
                title_el = tr.select_one("td a") or tr.select_one("a[href*='/job/']")
                company_el = tr.select_one(".company-name") or tr.select_one(".company")
                if not title_el:
                    continue
                title = title_el.text.strip()
                company = company_el.text.strip() if company_el else ""
                text_for_kw = title + " " + company + " " + tr.text
                if keywords and not _match_keywords(text_for_kw, keywords):
                    continue
                href = title_el.get("href", "")
                url = f"https://web3.career{href}" if href.startswith("/") else href
                salary_el = tr.select_one(".salary") or tr.select_one("[class*='salary']")
                loc_el = tr.select_one(".location") or tr.select_one("td:nth-child(3)")
                jobs.append(Job(
                    title=title, company=company,
                    location=loc_el.text.strip() if loc_el else "Remote",
                    url=url, source="web3.career",
                    salary=salary_el.text.strip() if salary_el else "",
                    remote="remote" in (loc_el.text.lower() if loc_el else ""),
                ))
        except Exception as e:
            log.warning(f"web3.career/{url_path}: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: CryptoJobsList (scrape)
# ---------------------------------------------------------------------------

def scrape_cryptojobslist(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://cryptojobslist.com/")
        soup = BeautifulSoup(html, "lxml")
        for item in soup.select("[class*='job']") or soup.select("tr") or soup.select(".job-listing"):
            title_el = item.select_one("a[href*='/jobs/']") or item.select_one("h3 a")
            company_el = item.select_one(".company") or item.select_one("[class*='company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://cryptojobslist.com{href}"
            loc_el = item.select_one(".location") or item.select_one("[class*='location']")
            jobs.append(Job(
                title=title, company=company,
                location=loc_el.text.strip() if loc_el else "Remote",
                url=url, source="cryptojobslist",
                remote=True,
            ))
    except Exception as e:
        log.warning(f"cryptojobslist: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: CryptoJobs (scrape)
# ---------------------------------------------------------------------------

def scrape_cryptojobs(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://crypto.jobs")
        soup = BeautifulSoup(html, "lxml")
        for item in soup.select("[class*='job']") or soup.select(".job-listing") or soup.select("tr"):
            title_el = item.select_one("a[href*='/jobs/']") or item.select_one("h3 a") or item.select_one(".title a")
            company_el = item.select_one(".company") or item.select_one("[class*='company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://crypto.jobs{href}"
            jobs.append(Job(
                title=title, company=company, url=url,
                source="crypto.jobs", remote=True,
            ))
    except Exception as e:
        log.warning(f"crypto.jobs: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: hnhiring — Hacker News "Who's Hiring" (scrape)
# ---------------------------------------------------------------------------

def scrape_hnhiring(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://hnhiring.com/")
        soup = BeautifulSoup(html, "lxml")
        for row in soup.select("tr.job") or soup.select(".job-row"):
            title_el = row.select_one("a") or row.select_one(".title a")
            company_el = row.select_one(".company") or row.select_one(".poster")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://hnhiring.com{href}"
            jobs.append(Job(
                title=title, company=company, url=url,
                source="hnhiring", remote=True,
            ))
    except Exception as e:
        log.warning(f"hnhiring: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Dice (scrape, cloudflare likely)
# ---------------------------------------------------------------------------

def scrape_dice(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://www.dice.com/jobs?q=android&remote=true")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select("[data-testid='job-card']"):
            title_el = card.select_one("a[data-testid='job-search-job-detail-link']")
            company_el = card.select_one("p.mb-0.line-clamp-1.text-sm")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://www.dice.com{href}"
            loc_el = card.select_one("p.text-sm.font-normal")
            loc = loc_el.text.strip().split("•")[0].strip() if loc_el else "Remote"
            jobs.append(Job(
                title=title, company=company, location=loc,
                url=url, source="dice",
                remote=True,
            ))
    except Exception as e:
        log.warning(f"dice: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Wellfound / AngelList (scrape)
# ---------------------------------------------------------------------------

def scrape_wellfound(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://wellfound.com/jobs?remote=true")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select("[class*='job']") or soup.select(".styles__jobCard"):
            title_el = card.select_one("a[href*='/jobs/']") or card.select_one(".title a")
            company_el = card.select_one(".company-name") or card.select_one("[class*='company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://wellfound.com{href}"
            jobs.append(Job(
                title=title, company=company, url=url,
                source="wellfound", remote=True,
            ))
    except Exception as e:
        log.warning(f"wellfound: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Y Combinator Jobs
# ---------------------------------------------------------------------------

def scrape_yc(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://www.workatastartup.com/jobs")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select("div.grid.grid-cols-1 > div.flex.h-full"):
            title_el = card.select_one("a.text-base.font-semibold")
            company_el = card.select_one("a[href*='/companies/'] span.font-bold")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            text_for_kw = title + " " + company + " " + card.text
            if keywords and not _match_keywords(text_for_kw, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://www.workatastartup.com{href}"
            details_el = card.select_one("p.job-details")
            loc = "Remote"
            if details_el:
                parts = [s.strip() for s in details_el.text.split("•")]
                loc = parts[-1].strip() if len(parts) > 1 else parts[0].strip()
            jobs.append(Job(
                title=title, company=company, location=loc,
                url=url, source="ycjobs",
                remote="remote" in loc.lower(),
            ))
    except Exception as e:
        log.warning(f"yc: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Built In
# ---------------------------------------------------------------------------

def scrape_builtin(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://builtin.com/jobs/remote/dev-engineering/android")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select("[class*='job']") or soup.select(".job-card") or soup.select("article"):
            title_el = card.select_one("h3 a") or card.select_one("a[href*='/job/']")
            company_el = card.select_one(".company-name") or card.select_one("[class*='company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://builtin.com{href}"
            jobs.append(Job(
                title=title, company=company, url=url,
                source="builtin", remote=True,
            ))
    except Exception as e:
        log.warning(f"builtin: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: JustRemote
# ---------------------------------------------------------------------------

def scrape_justremote(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://justremote.co/remote-jobs")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select("[class*='job']") or soup.select(".job-card") or soup.select("a[href*='/remote-jobs/']"):
            title_el = card.select_one("h3") or card.select_one(".title") or card.select_one("span")
            company_el = card.select_one(".company") or card.select_one("[class*='company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = card.get("href", "") if card.name == "a" else ""
            if not href:
                parent = card.find_parent("a")
                href = parent.get("href", "") if parent else ""
            url = href if href.startswith("http") else f"https://justremote.co{href}"
            jobs.append(Job(
                title=title, company=company, url=url,
                source="justremote", remote=True,
            ))
    except Exception as e:
        log.warning(f"justremote: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Pangian
# ---------------------------------------------------------------------------

def scrape_pangian(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://pangian.com/job-search/")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select(".job-card") or soup.select("[class*='job']") or soup.select("article"):
            title_el = card.select_one("h3 a") or card.select_one("a[href*='/job/']")
            company_el = card.select_one(".company") or card.select_one("[class*='company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://pangian.com{href}"
            jobs.append(Job(
                title=title, company=company, url=url,
                source="pangian", remote=True,
            ))
    except Exception as e:
        log.warning(f"pangian: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Hired (reverse marketplace — scrape initial listing page)
# ---------------------------------------------------------------------------

def scrape_hired(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://hired.com/jobs?remote=true")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select("[class*='job']") or soup.select("[class*='card']"):
            title_el = card.select_one("a[href*='/job/']") or card.select_one(".title a")
            company_el = card.select_one(".company") or card.select_one("[class*='company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://hired.com{href}"
            jobs.append(Job(
                title=title, company=company, url=url,
                source="hired", remote=True,
            ))
    except Exception as e:
        log.warning(f"hired: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Source: Stack Overflow Jobs (archive via scrape)
# ---------------------------------------------------------------------------

def scrape_stackoverflow(s: Scraper, keywords: str = "") -> list[Job]:
    jobs = []
    try:
        html = s.get("https://stackoverflow.com/jobs?r=true")
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select(".job-card") or soup.select("[class*='job']") or soup.select(".listResults > div"):
            title_el = card.select_one("a[data-jobid]") or card.select_one("h2 a") or card.select_one("a.s-link")
            company_el = card.select_one(".company") or card.select_one("[class*='company']")
            if not title_el:
                continue
            title = title_el.text.strip()
            company = company_el.text.strip() if company_el else ""
            if keywords and not _match_keywords(title + " " + company, keywords):
                continue
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://stackoverflow.com{href}"
            jobs.append(Job(
                title=title, company=company, url=url,
                source="stackoverflow", remote=True,
            ))
    except Exception as e:
        log.warning(f"stackoverflow: {e}")
    return jobs


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _match_keywords(text: str, keywords: str) -> bool:
    if not keywords:
        return True
    text_lower = text.lower()
    return any(kw.strip().lower() in text_lower for kw in keywords.split() if kw.strip())


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SOURCES: dict[str, callable] = {
    # APIs (free, no key required)
    "remoteok": scrape_remoteok,
    "remotive": scrape_remotive,
    "arbeitnow": scrape_arbeitnow,
    "himalayas": scrape_himalayas,
    "jobicy": scrape_jobicy,
    "4dayweek": scrape_4dayweek,
    # Scrape (server-rendered or playwright fallback)
    "weworkremotely": scrape_weworkremotely,
    "web3.career": scrape_web3career,
    "cryptojobslist": scrape_cryptojobslist,
    "crypto.jobs": scrape_cryptojobs,
    "builtin": scrape_builtin,
    "justremote": scrape_justremote,
    "dice": scrape_dice,
    "ycjobs": scrape_yc,
    "remote.co": scrape_remoteco,
}


def crawler_job_to_ats(job: Job) -> dict:
    combined = job.title + " " + job.description
    tech_keywords = _extract_tech_keywords(combined)
    if job.tags:
        tech_keywords.extend(t for t in job.tags if len(t) > 2)
    return {
        "title": job.title,
        "company": job.company,
        "tech_stack": list(set(tech_keywords))[:30],
        "required_skills": [],
        "location": job.location,
        "url": job.url,
        "source": job.source,
        "salary": job.salary,
    }

def _extract_tech_keywords(text: str) -> list[str]:
    stop_words = {
        "and", "the", "with", "for", "our", "their", "your", "its",
        "knowledge", "background", "hands", "familiarity", "proficiency",
        "understanding", "experience", "ability", "including", "across",
        "through", "within", "between", "under", "over", "into", "about",
    }
    locality = {
        "United States", "North America", "South America", "Latin America",
        "EMEA", "APAC", "San Francisco", "New York", "Los Angeles",
        "Chicago", "Austin", "Seattle", "Boston", "Denver", "Portland",
        "Miami", "Atlanta", "Dallas", "Houston", "London", "Berlin",
        "Paris", "Amsterdam", "Toronto", "Vancouver", "Sydney", "Singapore",
        "California", "Texas", "New York City",
    }
    biz = {
        "About", "Job Type", "Full Time", "Part Time", "Contract", "Description",
        "Qualifications", "Requirements", "Responsibilities", "Location", "Salary",
        "Perks", "Benefits", "Apply Now", "Learn More", "Share", "Save",
        "Company", "Team", "Role", "Position", "Level", "Overview", "Posted",
        "Hiring", "Readily", "Demonstrate", "Coordinate", "Build", "Include",
        "Haves", "Includes", "Opportunity", "Success", "Founded", "Headquarters",
        "Industries", "Follow", "Twitter", "LinkedIn", "GitHub", "Website",
    }
    # Only extract phrases that look like genuine tech terms
    result = []

    # 1) Known multi-word tech terms (exact match)
    known_tech_phrases = {
        # Mobile
        "Jetpack Compose", "Clean Architecture", "Android SDK", "Android Studio",
        "Material Design", "Google Play", "Push Notification", "Dependency Injection",
        "Unit Test", "UI Test", "Code Review", "Version Control",
        "Continuous Integration", "Continuous Delivery", "CI/CD",
        "REST API", "GraphQL API", "WebSocket", "Background Service",
        "Machine Learning", "Deep Learning", "Computer Vision", "Natural Language",
        "Image Processing", "Real Time", "Cross Platform",
        # General
        "Agile Development", "Software Development", "Full Stack", "Front End",
        "Back End", "Software Engineering", "System Design", "Cloud Computing",
        "Microservices", "API Design", "Test Driven", "Object Oriented",
    }
    known_singles = {
        # Mobile
        "Kotlin", "Java", "Android", "Jetpack", "Compose", "Firebase",
        "Retrofit", "Room", "Hilt", "Dagger", "OkHttp", "WorkManager",
        "JUnit", "MockK", "CameraX", "Espresso", "Coil", "Glide",
        "ExoPlayer", "Coroutines", "Flow", "MVVM", "MVI", "NDK",
        "Gradle", "Fastlane", "ProGuard", "R8", "TFLite", "MLKit",
        "Play Services", "Material", "ConstraintLayout", "RecyclerView",
        "ViewBinding", "DataBinding", "Navigation", "Paging", "Hilt",
        # Languages
        "Python", "JavaScript", "TypeScript", "Dart", "Swift", "Go",
        "Rust", "C++", "SQL", "HTML", "CSS", "Shell",
        # Web/Backend
        "React", "Angular", "Vue", "Node", "Django", "Flask", "Spring",
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Linux",
        "Nginx", "Redis", "Kafka", "RabbitMQ", "MySQL", "PostgreSQL",
        "MongoDB", "Elasticsearch", "Terraform", "Ansible", "Jenkins",
        "GitHub Actions", "CircleCI", "GitLab", "SonarQube",
        # ML/AI
        "TensorFlow", "PyTorch", "ONNX", "OpenCV", "Scikit", "Pandas",
        "NumPy", "Jupyter", "CNN", "RNN", "LSTM", "RAG", "LLM",
        "OpenAI", "LangChain", "Llama", "Vector", "Embedding",
        # Other
        "Flutter", "GraphQL", "WebSocket", "REST", "JSON", "XML",
        "Protobuf", "gRPC", "OAuth", "JWT", "SSL", "TLS",
        "Agile", "Scrum", "Kanban", "Git", "GitHub", "GitLab",
    }

    # Check for known multi-word tech terms in the text
    text_lower = text.lower()
    for phrase in known_tech_phrases:
        if phrase.lower() in text_lower:
            result.append(phrase)

    # Check for known single-word tech terms
    for kw in known_singles:
        if kw.lower() in text_lower:
            result.append(kw)

    return list(set(result))


def deduplicate(jobs: list[Job]) -> list[Job]:
    seen = set()
    out = []
    for j in jobs:
        key = (j.title.lower().strip(), j.company.lower().strip(), j.url)
        if key not in seen:
            seen.add(key)
            out.append(j)
    return out


def main():
    ap = argparse.ArgumentParser(description="Remote job aggregator — 50+ sources, multi-bypass")
    ap.add_argument("--keywords", "-k", default="android", help="Keywords to filter (space-separated, any-match)")
    ap.add_argument("--sources", "-s", default="all", help="Comma-separated sources: " + ",".join(SOURCES.keys()) + " or 'all'")
    ap.add_argument("--output", "-o", default="jobs.json", help="Output JSON path")
    ap.add_argument("--proxy", "-p", default="", help="Proxy URL (e.g. http://user:pass@host:port)")
    ap.add_argument("--captcha-key", "-c", default="", help="2captcha/anticaptcha API key")
    args = ap.parse_args()

    s = Scraper(proxy=args.proxy, captcha_key=args.captcha_key)
    all_jobs: list[Job] = []

    selected = list(SOURCES.keys()) if args.sources == "all" else [x.strip() for x in args.sources.split(",") if x.strip()]

    for name in selected:
        if name not in SOURCES:
            log.warning(f"Unknown source: {name}")
            continue
        log.info(f"Scraping {name}...")
        try:
            jobs = SOURCES[name](s, keywords=args.keywords)
            all_jobs.extend(jobs)
            log.info(f"  -> {len(jobs)} jobs from {name}")
        except Exception as e:
            log.error(f"  -> ERROR scraping {name}: {e}")

    all_jobs = deduplicate(all_jobs)
    log.info(f"\nTotal unique jobs: {len(all_jobs)}")

    output_path = args.output
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump([asdict(j) for j in all_jobs], f, indent=2, default=str)
    log.info(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
