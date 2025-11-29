import os
import json
import time
import requests
from dotenv import load_dotenv
from pyairtable import Table

# === Config ===
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID          = os.getenv("AIRTABLE_BASE_ID")
TABLE_ID         = "tblnfIj6fZyKhtnkL"

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

# === Template ===
CHAPTER_TEMPLATE = {
  "Chapters": [
    {
      "title": "Introduction",
      "prompt": "Write a concise and institutional-grade 'Introduction' for an investment report on {{Company Name}}, a leading company in the {{Sector}} sector and {{Industry}} industry. Summarize its origin, historical development, mission, and core business activities. Highlight its current strategic focus and global relevance. Conclude by stating the objective of the report for long-term investors. Use only current, verifiable information. Every factual claim must include a clickable source hyperlink with the publication date. Do not include any conditional phrases, bracketed citations, or unlinked sources."
    },
    {
      "title": "Business Overview and Strategic Positioning",
      "prompt": "Write a comprehensive 'Business Overview and Strategic Positioning' section for {{Company Name}}. Break down its business lines or segments, listing key products and services. Quantify relevant KPIs such as revenue share, customer base, or R&D spend. Identify three core competitive advantages and explain how each contributes to sustained growth or margin protection. Cite all data points with clickable hyperlinks and publication dates. Avoid formula explanations or conditional phrasing."
    },
    {
      "title": "Industry and Competitive Landscape",
      "prompt": "Develop an 'Industry and Competitive Landscape' section for the {{Industry}} industry. Report the current market size and projected growth rate using concrete figures. Name 4–6 direct competitors and compare their positions. Highlight two industry trends (e.g., technology, regulation, consolidation). Identify structural barriers to entry and explain how {{Company Name}} is positioned to overcome them. Every claim must be supported with a hyperlink to a credible source, including publication date. Do not use bracketed references or unlinked citations."
    },
    {
      "title": "Macroeconomic and Regulatory Environment",
      "prompt": "Write a 'Macroeconomic and Regulatory Environment' section for {{Company Name}}. Provide current macro data affecting the {{Industry}} industry (e.g., interest rate, inflation, GDP growth). List major regulatory bodies and relevant standards or compliance frameworks (e.g., NAIC, ISO, GDPR). Describe one supply chain pressure with measurable business impact. Close with implications for {{Company Name}}’s strategic or financial planning. Include full hyperlinks and publication dates for all quantitative or regulatory references. Avoid generic summaries or unlinked source mentions."
    },
    {
      "title": "Financial Statement Analysis",
      "prompt": "Write a 'Financial Statement Analysis' for {{Company Name}} using actual trailing twelve-month figures. Include revenue, gross margin, net margin, operating cash flow, and one key profitability ratio (e.g., ROE, ROA). Report all values in USD millions and provide a source hyperlink for each figure, with its publication date clearly shown. Do not include formulas, derivations, or speculative projections. Use only verified final results."
    },
    {
      "title": "Capital Structure and Liquidity",
      "prompt": "Write a 'Capital Structure and Liquidity' section for {{Company Name}}. Report total debt, total equity, D/E ratio, cash reserves, current ratio, and interest coverage ratio with exact values. Explain what these figures imply about the company’s balance sheet health. Each metric must be sourced via a clickable link with a publication date. Do not use placeholders or unlinked source names."
    },
    {
      "title": "Valuation Analysis – Multiples Approach",
      "prompt": "Write a 'Valuation Analysis – Multiples Approach' for {{Company Name}}. Report the company’s current P/E, EV/EBITDA, and P/B ratios. Compare each to the median values of 4–6 relevant peers (list peer names). Calculate and explain the implied equity value or enterprise value where applicable (no formulas). Support every multiple and result with a clickable data source and publication date. Avoid assumptions, brackets, or citations without hyperlinks."
    },
    {
      "title": "Valuation Analysis – Discounted Cash Flow (DCF)",
      "prompt": "Write a 'Valuation Analysis – Discounted Cash Flow (DCF)' for {{Company Name}}. Clearly state your assumptions: revenue growth rate, WACC, terminal growth, and free cash flow margin. Use specific values and cite the source for each input with a clickable hyperlink and publication date. Present the final intrinsic value per share — no derivations or steps, just the output. Avoid speculative language or placeholders."
    },
    {
      "title": "Intrinsic Value and Upside Potential",
      "prompt": "Generate an 'Intrinsic Value and Upside Potential' section for {{Company Name}}. Compare the calculated intrinsic value per share to the current market price. Compute upside/downside as a percentage. Include the margin of safety (based on valuation gap). Every figure must be accompanied by a source hyperlink and publication date. Do not include derivations, speculative text, or citation placeholders."
    },
    {
      "title": "ESG Profile and Sustainability Initiatives",
      "prompt": "Write an 'ESG Profile and Sustainability Initiatives' section for {{Company Name}}. Provide one concrete environmental initiative (e.g., emissions reduction, recycling), one social program (e.g., DEI, philanthropy), and one governance practice (e.g., board diversity, anti-corruption). Use measurable targets or outcomes when possible. Support each initiative with a clickable source and publication date. Avoid generic summaries or unlinked claims."
    },
    {
      "title": "Analyst Sentiment and Institutional Ownership",
      "prompt": "Write an 'Analyst Sentiment and Institutional Ownership' section for {{Company Name}}. State the latest consensus analyst rating distribution (e.g., % Buy, Hold, Sell) and average price target. List the top three institutional shareholders and their percentage ownership. Every data point must include a clickable hyperlink and publication date. Do not use placeholders, estimated values, or citation brackets."
    },
    {
      "title": "Earnings Surprises and Forward Guidance",
      "prompt": "Write an 'Earnings Surprises and Forward Guidance' section for {{Company Name}}. Report actual vs. estimated EPS and revenue for the last two quarters, showing both surprise percentages. Summarize management’s forward guidance including expected EPS, revenue, or margin changes. Cite each figure with a clickable source and publication date. Avoid conditional text, meta explanations, or unlinked sources."
    },
    {
      "title": "Risk Factors and Stress Testing",
      "prompt": "Write a 'Risk Factors and Stress Testing' section for {{Company Name}}. Identify one market risk, one operational risk, and one regulatory risk with quantified impacts (e.g., −5% to revenue). Simulate three stress-test scenarios with final projected revenue or net income. Each result must be supported with a clickable source and publication date. Do not include formulas, placeholders, or theoretical commentary."
    },
    {
      "title": "Scenario‑Based Valuation Thesis",
      "prompt": "Write a 'Scenario-Based Valuation Thesis' for {{Company Name}}. Define Bull, Base, and Bear case price targets, each with a brief rationale and probability weight (e.g., 20%, 60%, 20%). Every target and probability must be grounded in current market data with a clickable hyperlink and publication date. Avoid meta language, formulas, or unlinked references."
    },
    {
      "title": "(External Consensus) Market Investment Opinion",
      "prompt": "Write an '(External Consensus) Market Investment Opinion' section for {{Company Name}}. Provide the consensus investment rating (Buy/Hold/Sell) and average price target. List three supporting takeaways such as recent analyst upgrades, institutional sentiment, or valuation signals — each backed by a clickable hyperlink and publication date. Avoid generic phrasing, speculative remarks, or unlinked summaries."
    }
  ]
}

# === Run Perplexity
def run_perplexity(prompt):
    payload = {
        "model": "sonar",
        "max_tokens": 4000,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ]
    }
    response = requests.post(PERPLEXITY_URL, headers=HEADERS, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# === Start research
table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_ID)
records = table.all()

ready = [r["fields"] for r in records if r.get("fields", {}).get("analysis", "").lower() == "ready"]

for company in ready:
    company_name = company.get("company_name", "").strip()
    sector       = company.get("sector", "").strip()
    industry     = company.get("industry", "").strip()

    print(f"\n🚀 Researching: {company_name}")

    result = {
        "company": company_name,
        "sector": sector,
        "industry": industry,
        "chapters": []
    }

    for chapter in CHAPTER_TEMPLATE["Chapters"]:
        title = chapter["title"]
        prompt = chapter["prompt"]\
            .replace("{{Company Name}}", company_name)\
            .replace("{{Sector}}", sector)\
            .replace("{{Industry}}", industry)

        print(f"📌 {title}")
        try:
            content = run_perplexity(prompt)
        except Exception as e:
            content = f"ERROR: {str(e)}"
            print(f"❌ {title}: {e}")

        result["chapters"].append({"title": title, "content": content})

    # Save JSON
    os.makedirs("Research Assistant", exist_ok=True)
    out_path = os.path.join("Research Assistant", f"{company_name.replace(' ', '_')}_Research.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Done: {out_path}")
