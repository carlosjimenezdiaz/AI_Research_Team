import os
import requests
import json
from dotenv import load_dotenv

# === Cargar variables desde .env ===
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

# === Configuración Airtable ===
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_ID = os.getenv("AIRTABLE_TABLE_ID")
VIEW_ID = os.getenv("AIRTABLE_VIEW_ID")

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}"
}

def fetch_ready_records():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
    params = {"view": VIEW_ID}
    all_records = []
    offset = None

    while True:
        if offset:
            params["offset"] = offset

        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        for record in data.get("records", []):
            fields = record.get("fields", {})
            analysis_value = fields.get("analysis", "")

            # Manejo robusto para string o lista
            if isinstance(analysis_value, list):
                is_ready = any(str(v).strip().upper() == "READY" for v in analysis_value)
            else:
                is_ready = str(analysis_value).strip().upper() == "READY"

            if is_ready:
                all_records.append(fields)

        offset = data.get("offset")
        if not offset:
            break

    print(f"✅ Found {len(all_records)} records with analysis == READY")
    return all_records

# === MAIN TEST ===
if __name__ == "__main__":
    try:
        records = fetch_ready_records()
        print("\n📘 Companies ready for research:")
        for r in records:
            print(f"🔹 {r.get('symbol', 'No Symbol')} | {r.get('company_name', 'No Name')} | Sector: {r.get('sector', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")
