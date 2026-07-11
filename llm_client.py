import json
import urllib.request
import urllib.error
from typing import Optional


API_BASE = "http://localhost:8080/v1"


def list_models() -> list[str]:
    try:
        req = urllib.request.Request(f"{API_BASE}/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [m["id"] for m in data.get("data", [])]
    except Exception as e:
        raise ConnectionError(f"Cannot connect to llama-server at {API_BASE}: {e}")


def generate_cover_letter(
    job_posting: str,
    cv_summary: str,
    cv_skills: list[str],
    cv_experience: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 2000,
) -> str:
    models = list_models()
    if not models:
        raise RuntimeError("No models available on llama-server")
    model = model or models[0]

    exp_text = "\n".join(
        f"- {exp['role']} at {exp['company']} ({exp['period']}):\n"
        + "\n".join(f"  • {h}" for h in exp["highlights"])
        for exp in cv_experience
    )

    system_prompt = (
        "You are a senior Android engineer writing a cover letter to a fellow engineer or hiring manager. "
        "Write the body only — no greeting, no signature, no subject line. "
        "Write 3 to 4 flowing paragraphs with no bullet points, no dashes, no lists, and no markdown. "
        "Use natural sentences that sound like a real person wrote them, not a template. "
        "Reference specific technologies and achievements from the candidate's experience, "
        "but weave them into full sentences naturally. "
        "Do not use phrases like 'I am writing to apply' or 'I am excited to apply' — "
        "just speak directly about your experience and why it fits the role."
    )

    user_prompt = f"""JOB POSTING:
{job_posting}

CANDIDATE SUMMARY:
{cv_summary}

KEY SKILLS:
{', '.join(cv_skills)}

EXPERIENCE:
{exp_text}

Write the cover letter body paragraphs that connect this candidate's experience to the job requirements."""

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            content = result["choices"][0]["message"]["content"].strip()
            return content
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"LLM request failed ({e.code}): {body}")
    except Exception as e:
        raise RuntimeError(f"LLM request failed: {e}")
