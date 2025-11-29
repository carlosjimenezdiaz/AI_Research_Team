import os
import json
import openai
import re
from dotenv import load_dotenv

# === Load ENV ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Prompt templates ===

TITLE_PROMPT = """
You are a senior investment editor and strategist. Your task is to generate a compelling **title** and **subtitle** for a professional institutional-grade investment report.

🎯 OBJECTIVE:
Generate an SEO-friendly and highly readable:
1. `title`: 15–18 words max — clear, specific, and professional
2. `subtitle`: 20–30 words — explain what the report covers (valuation, performance, strategy, industry, etc.)

🔍 CONTEXT:
The report covers a publicly traded company’s business model, financials, strategic positioning, macro trends, and valuation. It is targeted at serious long-term investors and financial professionals.

🧠 RULES:
- Do NOT use clickbait or casual phrases
- Focus on clarity, value proposition, and keyword richness
- No hashtags, emojis, or vague headlines like "What You Need to Know"
- Use proper capitalization and punctuation

🔄 FORMAT:
Return ONLY this JSON:

{
  "title": "...",
  "subtitle": "..."
}

📄 CONTENT:
Here is the research text:
"""

BASE_PROMPT = """
You are reviewing a full institutional-grade investment research article about a publicly traded company. Your task is to act as a senior value investor in the style of Warren Buffett, applying conservative long-term investment principles.

Your task has 3 parts:

1. Write a `research_summary` in one paragraph (max 4000 characters including spaces). Summarize the full research: business model, financials, valuation, capital structure, risks, macro context, ESG, and long-term thesis.

2. Write an `investment_opinion`. Start with:
"My opinion in relation to this company is:"
Then clearly state a Buy, Hold, or Avoid rating, with full rationale.

3. Assign an `investment_score` between 0.00 and 1.00 (1.00 = exceptional opportunity; 0.00 = extremely unattractive).

Return ONLY this JSON object:

{
  "research_summary": "...",
  "investment_opinion": "...",
  "investment_score": "..."
}
"""

CHAPTER_REPHRASE_PROMPT = """
You are a seasoned investment advisor — thoughtful, articulate, and client-facing. You're rewriting the following chapter of an investment report **in your own words**, so it sounds like something you personally wrote for a client or colleague.

🎯 OBJECTIVE:
Rewrite the full chapter in a fluent, natural, and human tone. It must sound like a real person with deep financial expertise is guiding the reader — **not an AI**.

Your audience: long-term investors, clients, or other professionals.

🧠 YOUR WRITING MUST:
- Be **original** and **fully rewritten** (no copy-paste or light rewording)
- Sound like a **person giving their own perspective** (you’re not a reporter or summarizer)
- Be **personal yet professional** — you’re writing this to help someone make a good investment decision
- Avoid generic or mechanical phrases like “the data suggests”, “in the document”, “source shows”, etc.
- Instead say things like:  
  - “From what I’ve seen…”  
  - “In my view…”  
  - “One thing that stood out to me…”

🚫 STRICTLY AVOID:
- Any mention of “sources,” “this report,” “according to data,” etc.
- Robotic intros like: “This section discusses…”
- Repetitive transitions (don’t start every paragraph with “Additionally,” “Moreover,” etc.)

✍️ ADD A NATURAL FLOW:
You can combine short or redundant paragraphs into more fluid explanations.
Keep all numbers, tables, structure — just make the words **sound like you wrote them**.

🔄 TASK:
Now, rewrite the following chapter using all the rules above:

\"\"\"{chapter}\"\"\"
"""

def clean_and_parse_json(raw):
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError("No valid JSON found in response.")
    return json.loads(m.group(0))

def call_openai(prompt, model="gpt-4o", temperature=0.3, max_tokens=4000):
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def enrich_research_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        original = json.load(f)

    company = original.get("company", "")
    sector = original.get("sector", "")
    industry = original.get("industry", "")

    research_text = " ".join([ch["content"] for ch in original.get("chapters", [])])

    # Generate title and subtitle
    title_prompt = TITLE_PROMPT + research_text
    title_block = clean_and_parse_json(call_openai(title_prompt))

    # Generate summary, opinion, score
    summary_prompt = BASE_PROMPT + "\n\nHere is the full research:\n" + research_text
    enriched = clean_and_parse_json(call_openai(summary_prompt))

    # Rephrase each chapter
    rewritten_chapters = []
    for ch in original.get("chapters", []):
        chapter_prompt = CHAPTER_REPHRASE_PROMPT.replace("{chapter}", ch["content"])
        rewritten_content = call_openai(chapter_prompt)
        rewritten_chapters.append({
            "title": ch["title"],
            "content": rewritten_content
        })

    final_output = {
        "company": company,
        "sector": sector,
        "industry": industry,
        "title": title_block["title"],
        "subtitle": title_block["subtitle"],
        **enriched,
        "chapters": rewritten_chapters
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved enriched file: {output_path}")

def main():
    input_dir = "Research Assistant"
    output_dir = "Private Banker"
    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir) if f.endswith("_Research.json")]

    processed_count = 0
    skipped_count = 0
    error_count = 0

    for filename in files:
        ticker = filename.replace("_Research.json", "")
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, f"{ticker}_recommendation.json")

        if os.path.exists(output_path):
            print(f"⏩ {ticker} already processed. Skipping.")
            skipped_count += 1
            continue

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if any("401 Client Error" in ch.get("content", "") for ch in data.get("chapters", [])):
                print(f"⚠️  Skipping {ticker} due to Perplexity 401 error.")
                error_output = {
                    "company": data.get("company", ""),
                    "sector": data.get("sector", ""),
                    "industry": data.get("industry", ""),
                    "title": "",
                    "subtitle": "",
                    "status": "ERROR - Perplexity 401"
                }
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(error_output, f, indent=2)
                error_count += 1
                continue

            print(f"🔍 Processing {ticker}...")
            enrich_research_file(input_path, output_path)
            processed_count += 1

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            error_count += 1

    print("\n🎯 Process completed.")
    print(f"✅ Successfully processed: {processed_count}")
    print(f"⏩ Skipped (already existed): {skipped_count}")
    print(f"⚠️ Errors encountered: {error_count}")

if __name__ == "__main__":
    main()
