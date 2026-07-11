import json
import re
from collections import Counter
from typing import Optional

from data.personal_info import PERSONAL_INFO
from cv_builder import CVBuilder


class ATSScorer:
    WEIGHTS = {
        "keyword_presence": 30,
        "keyword_frequency": 15,
        "keyword_density": 10,
        "section_completeness": 15,
        "formatting": 10,
        "action_verbs": 10,
        "quantifiable_achievements": 10,
    }

    ACTION_VERBS = [
        "achieved", "architected", "built", "created", "delivered", "designed",
        "developed", "established", "implemented", "improved", "increased",
        "integrated", "introduced", "launched", "led", "managed", "mentored",
        "migrated", "optimized", "orchestrated", "pioneered", "reduced",
        "redesigned", "resolved", "restructured", "streamlined", "strengthened",
        "transformed", "upgraded",
    ]

    QUANTIFIABLE_PATTERNS = [
        r"\d+%", r"\d+K\+?", r"\d+M\+?", r"\d+\.\d+",
        r"\d+ years?", r"\d+x",
        r"\d+-\d+", r"\d+ users?", r"\d+ clients?",
        r"\d+ projects?", r"\d+ screens?", r"\d+ countries?",
        r"\d+\+",
    ]

    def __init__(self, cv_builder: Optional[CVBuilder] = None):
        self.builder = cv_builder or CVBuilder()
        self.info = self.builder.info

    @property
    def _full_text(self) -> str:
        parts = [self.info["summary"]]
        parts.extend(self.info["skills"])
        for exp in self.info["experience"]:
            parts.extend(exp["highlights"])
        for p in self.info.get("latest_portfolio", []):
            parts.extend(p.get("highlights", []))
        for p in self.info.get("projects", []):
            parts.extend(p.get("highlights", []))
        for edu in self.info.get("education", []):
            for val in edu.values():
                if isinstance(val, str) and val:
                    parts.append(val)
        return " ".join(parts).lower()

    def score_keyword_presence(self, keywords: list[str]) -> tuple[float, list[str], list[str]]:
        text = self._full_text
        found = []
        missing = []
        for kw in keywords:
            if re.search(re.escape(kw), text, re.IGNORECASE):
                found.append(kw)
            else:
                missing.append(kw)
        if not keywords:
            return 0, [], []
        score = (len(found) / len(keywords)) * self.WEIGHTS["keyword_presence"]
        return round(score, 1), found, missing

    def score_keyword_frequency(self, keywords: list[str]) -> tuple[float, dict]:
        text = self._full_text
        freq = {}
        for kw in keywords:
            c = len(re.findall(re.escape(kw), text, re.IGNORECASE))
            if c > 0:
                freq[kw] = c
        avg_freq = sum(freq.values()) / len(keywords) if keywords else 0
        target = 2.0
        ratio = min(avg_freq / target, 1.0)
        score = ratio * self.WEIGHTS["keyword_frequency"]
        return round(score, 1), freq

    def score_keyword_density(self, keywords: list[str]) -> float:
        return self.keyword_density_from_list(keywords)

    def score_section_completeness(self) -> float:
        required = ["summary", "skills", "experience", "education"]
        optional = ["certifications", "languages"]
        present = 0
        for s in required:
            if self.info.get(s):
                present += 1
        for s in optional:
            if self.info.get(s):
                present += 0.5
        total = len(required) + len(optional) * 0.5
        score = (present / total) * self.WEIGHTS["section_completeness"]
        return round(score, 1)

    def score_formatting(self) -> float:
        score = self.WEIGHTS["formatting"]
        text = self._full_text
        deductions = 0
        if len(self.info["name"]) < 2:
            deductions += 3
        if not self.info["email"]:
            deductions += 2
        if not self.info["phone"]:
            deductions += 1
        if len(self.info["experience"]) == 0:
            deductions += 3
        return max(0, score - deductions)

    def score_action_verbs(self) -> tuple[float, list[str]]:
        text = self._full_text
        found_verbs = []
        for verb in self.ACTION_VERBS:
            if re.search(rf"\b{re.escape(verb)}\w*\b", text, re.IGNORECASE):
                found_verbs.append(verb)
        ratio = min(len(found_verbs) / 5, 1.0)
        score = ratio * self.WEIGHTS["action_verbs"]
        return round(score, 1), found_verbs

    def score_quantifiable_achievements(self) -> tuple[float, list[str]]:
        text_parts = []
        for exp in self.info["experience"]:
            text_parts.extend(exp["highlights"])
        for proj in self.info.get("latest_portfolio", []):
            text_parts.extend(proj.get("highlights", []))
        for proj in self.info.get("projects", []):
            text_parts.extend(proj.get("highlights", []))
        text = " ".join(text_parts).lower()
        found = []
        for pat in self.QUANTIFIABLE_PATTERNS:
            matches = re.findall(pat, text)
            if matches:
                found.extend(matches)
        unique_found = len(set(found))
        ratio = min(unique_found / 4, 1.0)
        score = ratio * self.WEIGHTS["quantifiable_achievements"]
        return round(score, 1), found

    def score_for_job(self, job_posting: dict) -> dict:
        all_keywords = []
        all_keywords.extend(job_posting.get("tech_stack", []))
        all_keywords.extend(
            [kw for req in job_posting.get("required_skills", [])
             for kw in self._extract_keywords(req)]
        )
        all_keywords = list(set(kw.strip() for kw in all_keywords if kw.strip()))

        kw_presence, found, missing = self.score_keyword_presence(all_keywords)
        kw_freq, freq = self.score_keyword_frequency(all_keywords)
        kw_density = self.keyword_density_from_list(all_keywords)
        sections = self.score_section_completeness()
        fmt = self.score_formatting()
        verbs, found_verbs = self.score_action_verbs()
        quant, quant_found = self.score_quantifiable_achievements()

        total = round(kw_presence + kw_freq + kw_density + sections + fmt + verbs + quant, 1)

        return {
            "total_score": total,
            "max_score": sum(self.WEIGHTS.values()),
            "breakdown": {
                "Keyword Presence": {"score": kw_presence, "max": self.WEIGHTS["keyword_presence"]},
                "Keyword Frequency": {"score": kw_freq, "max": self.WEIGHTS["keyword_frequency"]},
                "Keyword Density": {"score": kw_density, "max": self.WEIGHTS["keyword_density"]},
                "Section Completeness": {"score": sections, "max": self.WEIGHTS["section_completeness"]},
                "Formatting": {"score": fmt, "max": self.WEIGHTS["formatting"]},
                "Action Verbs": {"score": verbs, "max": self.WEIGHTS["action_verbs"]},
                "Quantifiable Achievements": {"score": quant, "max": self.WEIGHTS["quantifiable_achievements"]},
            },
            "details": {
                "matched_keywords": found,
                "missing_keywords": missing,
                "keyword_frequencies": freq,
                "action_verbs_used": found_verbs,
                "quantifiable_found": quant_found,
            },
            "job_title": job_posting.get("title", ""),
            "company": job_posting.get("company", ""),
        }

    def keyword_density_from_list(self, keywords: list[str]) -> float:
        text = self._full_text
        words = text.split()
        if not words:
            return 0
        total_matches = sum(
            len(re.findall(re.escape(kw), text, re.IGNORECASE))
            for kw in keywords
        )
        density = total_matches / len(words)
        optimal = 0.05
        if density <= optimal:
            ratio = density / optimal
        else:
            ratio = max(0, 1.0 - (density - optimal) / optimal)
        return round(ratio * self.WEIGHTS["keyword_density"], 1)

    def _extract_keywords(self, text: str) -> list[str]:
        stop_words = {
            "and", "the", "with", "for", "our", "their", "your", "its",
            "deep", "excellent", "knowledge", "background", "hands",
            "familiarity", "proficiency", "understanding", "strong",
            "published", "bachelor", "fields", "degree", "related",
            "age", "experience", "all", "india", "only",
        }
        tech_terms = re.findall(r"\b[A-Z][a-zA-Z+#./]*(?:\s[A-Z][a-zA-Z+#./]*)*\b", text)
        result = []
        for term in tech_terms:
            t = term.strip()
            if not t or len(t) < 3:
                continue
            if t.lower() in stop_words:
                continue
            # Keep terms that look like tech keywords:
            # 2+ word phrases (e.g. "Jetpack Compose", "Clean Architecture")
            # OR single words that are clearly tech (capitalized, tech-sounding)
            words = t.split()
            if len(words) >= 2:
                result.append(t)
            elif len(words) == 1 and len(t) >= 4:
                # Only include single-word tech terms that look like tech
                techish = any(kw.lower() in t.lower() for kw in [
                    "kotlin", "java", "git", "sql", "api", "sdk", "ndk", "jni",
                    "ml", "ai", "mvvm", "mvi", "ci", "ui", "gpu", "cpu",
                    "rest", "http", "json", "xml", "rag", "cnn", "lstm",
                    "di", "db", "qa",
                ])
                if techish:
                    result.append(t)
                    continue
                common_tech_singles = {
                    "Kotlin", "Java", "Git", "Firebase", "Retrofit", "Room",
                    "Hilt", "Koin", "Dagger", "OkHttp", "WorkManager",
                    "Fastlane", "Jenkins", "Bitrise", "JUnit", "MockK",
                    "TFLite", "LiteRT", "ONNX", "WebSocket", "CameraX",
                    "Espresso", "Coil", "Glide", "ExoPlayer", "LeakCanary",
                    "Profiler", "Vulkan", "OpenCL", "Coroutines",
                    "Jetpack", "Material", "Agile", "Scrum", "Gradle",
                    "GraphQL", "Postman", "SonarQube", "Detekt",
                }
                if t in common_tech_singles:
                    result.append(t)
        return result

    def comprehensive_score(self, job_postings: list[dict]) -> dict:
        if not job_postings:
            return {"error": "No job postings provided"}
        scores = [self.score_for_job(job) for job in job_postings]
        avg_score = round(sum(s["total_score"] for s in scores) / len(scores), 1)
        all_missing = set()
        all_matched = set()
        for s in scores:
            all_matched.update(s["details"]["matched_keywords"])
            all_missing.update(s["details"]["missing_keywords"])
        return {
            "average_ats_score": avg_score,
            "max_score": sum(self.WEIGHTS.values()),
            "jobs_scored": len(scores),
            "score_distribution": {
                "90-100": sum(1 for s in scores if s["total_score"] >= 90),
                "80-89": sum(1 for s in scores if 80 <= s["total_score"] < 90),
                "70-79": sum(1 for s in scores if 70 <= s["total_score"] < 80),
                "60-69": sum(1 for s in scores if 60 <= s["total_score"] < 70),
                "below_60": sum(1 for s in scores if s["total_score"] < 60),
            },
            "globally_matched_keywords": sorted(all_matched),
            "globally_missing_keywords": sorted(all_missing),
            "suggestions": self._generate_suggestions(avg_score, all_missing, len(scores)),
        }

    def _generate_suggestions(self, avg_score: float, missing: set, total_jobs: int) -> list[str]:
        suggestions = []
        if avg_score < 70:
            suggestions.append(
                "Add more industry-standard keywords from actual job postings to your skills section"
            )
        elif avg_score < 80:
            suggestions.append(
                "Your CV is decent, but adding more specific Android technologies would boost ATS match rate"
            )
        if len(missing) > 10:
            suggestions.append(
                f"Consider adding these missing keywords: {', '.join(list(missing)[:10])}"
            )
        if total_jobs > 20 and avg_score >= 80:
            suggestions.append(
                "Strong match! Consider tailoring your summary to specific job types for even higher scores"
            )
        if len(self._full_text.split()) < 300:
            suggestions.append("Add more detail to your experience bullet points for better keyword coverage")
        return suggestions or ["Your CV is well-optimized for ATS!"]


class CVOptimizer:
    def __init__(self, cv_builder: CVBuilder):
        self.builder = cv_builder
        self.info = cv_builder.info

    def suggest_keywords_from_jobs(self, jobs: list[dict], top_n: int = 20) -> list[str]:
        keyword_counter = Counter()
        for job in jobs:
            for kw in job.get("tech_stack", []):
                if kw.strip():
                    keyword_counter[kw] += 1
            for req in job.get("required_skills", []):
                for kw in re.findall(r"\b[A-Z][a-zA-Z+#.]*\b", req):
                    if len(kw) >= 2:
                        keyword_counter[kw.lower()] += 1
        return [kw for kw, _ in keyword_counter.most_common(top_n)]

    def generate_optimized_cv(self, jobs: list[dict], output_path: str):
        suggestions = self.suggest_keywords_from_jobs(jobs)
        cv_text = f"""
{'='*60}
OPTIMIZED CV SUMMARY - ATS ENHANCED
{'='*60}

Use these keywords in your CV for better ATS matching:

Top Recommended Keywords (from {len(jobs)} job postings):
{', '.join(suggestions[:20])}

Sample Resume Bullet Points:

• Architected and delivered 4 major Android applications for banking and fintech clients using 
  Clean Architecture + MVVM, serving 50K+ MAU collectively

• Led migration of legacy XML-based apps to Jetpack Compose, reducing UI development time by 40% 
  and improving developer velocity

• Established CI/CD pipelines with GitHub Actions + Fastlane, cutting release cycles from 2 weeks 
  to 2 days with automated testing and distribution

• Implemented comprehensive test coverage with JUnit, MockK, and Espresso, improving coverage 
  from 15% to 85%

• Reduced app crash rate by 60% through systematic performance profiling with Android Profiler 
  and LeakCanary

• Built offline-first architecture using Room, WorkManager, and sync strategies handling 
  10K+ transactions during network outages

• Integrated multiple payment gateways (Midtrans, Xendit) with secure tokenization

• Mentored 3 junior developers through code reviews, pair programming, and tech talks

Optimization Suggestions:
• Use action verbs like "Architected", "Led", "Delivered", "Optimized", "Reduced"
• Include numbers and percentages in every bullet point
• Target 3-6% keyword density for the most common job posting terms
• Ensure all section headings use standard ATS-friendly names
"""
        with open(output_path, "w") as f:
            f.write(cv_text)
        return output_path
