"""
LLM integration (Concept 6): one narrow job — extract deadline + eligibility
from pasted scholarship text — behind an endpoint, with input validation
and a cost log. Uses OpenRouter (same pattern as BE-07 /enrich).
"""
import os
import json
import time
import httpx

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

SYSTEM_PROMPT = (
    "You extract structured facts from scholarship program descriptions. "
    "Given raw text, return ONLY a JSON object with keys: "
    "'deadline' (YYYY-MM-DD or null if not found), "
    "'eligibility' (one short sentence summarizing eligibility, or null). "
    "No preamble, no markdown fences, JSON only."
)


def _log_cost(prompt_tokens: int, completion_tokens: int, model: str):
    with open("llm_costs.log", "a") as f:
        f.write(
            f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
            f"model={model} prompt_tokens={prompt_tokens} "
            f"completion_tokens={completion_tokens}\n"
        )


def extract_deadline_and_eligibility(raw_text: str) -> dict:
    if not raw_text or len(raw_text.strip()) < 10:
        return {"deadline": None, "eligibility": None, "error": "input too short"}

    if not OPENROUTER_API_KEY:
        # Graceful degradation for local/demo runs without a key.
        _log_cost(0, 0, "none-no-api-key")
        return {"deadline": None, "eligibility": None, "error": "OPENROUTER_API_KEY not set"}

    try:
        resp = httpx.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": raw_text[:4000]},
                ],
                "temperature": 0,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        _log_cost(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), MODEL)

        content = data["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(content)
        return {"deadline": parsed.get("deadline"), "eligibility": parsed.get("eligibility")}
    except Exception as e:
        _log_cost(0, 0, f"error:{type(e).__name__}")
        return {"deadline": None, "eligibility": None, "error": str(e)}
