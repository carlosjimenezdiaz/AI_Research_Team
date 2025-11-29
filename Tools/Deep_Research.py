import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_URL     = "https://api.perplexity.ai/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
    "Content-Type": "application/json"
}

SYSTEM_PROMPT = """You are a real-time internet-connected research assistant. Your job is to return only factual, up-to-date, and verifiable information.
RULES:
1. DO NOT generate or fabricate data, statistics, or sources.
2. ONLY include facts that are backed by **real, working hyperlinks** from **reputable sources**.
3. Every claim or number **must include a clickable URL** in markdown format and the **exact publication date**.
4. You must place citations directly in the text using this format: [source](https://...) (Published: YYYY-MM-DD).
5. The entire response must be approximately 1000 words.
6. NEVER include broken, non-functional, paywalled, or unverifiable links.
7. If no reliable sources are found, say: "No recent or reliable data available."
8. NEVER speculate or invent any information."""

def run_perplexity_research(prompt: str, retries: int = 2, timeout: int = 120) -> tuple[str, dict]:
    payload = {
        "model": "sonar",
        "max_tokens": 4000,
        "temperature": 0.1,
        "messages": [
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": prompt}
        ]
    }

    for attempt in range(retries + 1):
        try:
            response = requests.post(PERPLEXITY_URL, headers=HEADERS, json=payload, timeout=timeout)
            response.raise_for_status()
            data    = response.json()
            content = data["choices"][0]["message"]["content"]
            usage   = data.get("usage", {})
            return content, usage

        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(10)
            else:
                raise

        except Exception as e:
            raise
