import os
import json

# === CONFIG ===
TOKEN_USAGE_FOLDER = "Token Usage"
PRICING = {
    "gpt-4o": {
        "input": 0.005,     # $5.00 per 1M input tokens => $0.005 per 1K
        "output": 0.015     # $15.00 per 1M output tokens => $0.015 per 1K
    },
    "sonar": {
        "total": 0.001      # $1.00 per 1M tokens => $0.001 per 1K
    }
}

USAGE_FILES = {
    "private_banker_token_usage.json": "gpt-4o",
    "perplexity_token_usage.json": "sonar"
}

# === Cálculo de costos ===
total_cost = 0.0
print("💰 Costo por archivo (detallado):\n")

for filename, model in USAGE_FILES.items():
    path = os.path.join(TOKEN_USAGE_FOLDER, filename)
    if not os.path.exists(path):
        print(f"⚠️  Archivo no encontrado: {filename}")
        continue

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    prompt_total = 0
    completion_total = 0
    total_tokens = 0

    if model == "gpt-4o":
        for record in data.values():
            if isinstance(record, dict):
                prompt_total += record.get("prompt_tokens", 0)
                completion_total += record.get("completion_tokens", 0)
            elif isinstance(record, int):
                # fallback if only total tokens are provided
                prompt_total += record // 2
                completion_total += record // 2
        cost = (prompt_total / 1000) * PRICING[model]["input"] + (completion_total / 1000) * PRICING[model]["output"]
        total_tokens = prompt_total + completion_total
        print(f"📄 {filename:<35} | Modelo: {model} | Prompt: {prompt_total:>6} | Completion: {completion_total:>6} | Total: {total_tokens:>6} | 💵 Costo: ${cost:.4f}")

    elif model == "sonar":
        for record in data.values():
            if isinstance(record, int):
                total_tokens += record
        cost = (total_tokens / 1000) * PRICING[model]["total"]
        print(f"📄 {filename:<35} | Modelo: {model} | Total: {total_tokens:>6} | 💵 Costo: ${cost:.4f}")

    total_cost += cost

# === Total ===
print("\n🔢 Costo total estimado:")
print(f"🧾 TOTAL: ${total_cost:.4f}")
