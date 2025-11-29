import os
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv
from pyairtable import Api

# === Configuración ===
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID          = os.getenv("AIRTABLE_BASE_ID")
DEST_TABLE       = os.getenv("AIRTABLE_RESEARCH_TABLE_ID")

# Carpetas locales
BASE_DIR      = os.path.dirname(__file__)
DIR_RESEARCH  = os.path.join(BASE_DIR, "Private Banker")
DIR_ERRORS    = os.path.join(BASE_DIR, "errors")

# Crear carpeta de errores si no existe
os.makedirs(DIR_ERRORS, exist_ok=True)

# Cliente Airtable
api        = Api(AIRTABLE_API_KEY)
dest_table = api.base(BASE_ID).table(DEST_TABLE)

# Fecha actual
today = datetime.today().strftime("%Y-%m-%d")

# === Subida de archivos desde Private Banker ===
for fn in os.listdir(DIR_RESEARCH):
    if not fn.endswith("_recommendation.json"):
        continue

    research_path = os.path.join(DIR_RESEARCH, fn)
    print(f"\n🚀 Procesando archivo: {fn}")

    try:
        with open(research_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo o parseando {fn}: {e}")
        continue

    # Campos generales
    company_name = json_data.get("company") or fn.replace("_recommendation.json", "").replace("_", " ").strip()
    sector       = json_data.get("sector", "")
    industry     = json_data.get("industry", "")
    title        = json_data.get("title", "").strip()
    status       = json_data.get("status", "").strip()

    # Nuevos campos
    research_summary    = json_data.get("research_summary", "").strip()
    investment_opinion  = json_data.get("investment_opinion", "").strip()
    raw_score = json_data.get("investment_score", "").strip()
    try:
        investment_score = float(raw_score)
    except Exception:
        investment_score = 0.0  # default when missing or invalid

    # Detectar errores
    is_error = (
        not title or
        status.startswith("ERROR") or
        not json_data.get("subtitle")
    )

    if is_error:
        payload = {
            "company_name":       company_name,
            "sector":             sector,
            "industry":           industry,
            "title":              "Missing",
            "html_content":       "Missing",
            "authors":            "Carlos Jimenez",
            "date_created":       "Missing",
            "flag":               "Error",
            "research_summary":   "Missing",
            "investment_opinion": "Missing",
            "investment_score":   "Missing"
        }

        try:
            destination_path = os.path.join(DIR_ERRORS, fn)
            shutil.move(research_path, destination_path)
            print(f"📦 Archivo con error movido a: {destination_path}")
        except Exception as e:
            print(f"❌ Error al mover archivo {fn} a carpeta de errores: {e}")

    else:
        try:
            with open(research_path, "r", encoding="utf-8") as f:
                json_str = f.read()

            payload = {
                "company_name":       company_name,
                "sector":             sector,
                "industry":           industry,
                "title":              title,
                "html_content":       json_str,
                "authors":            "Carlos Jimenez",
                "date_created":       today,
                "flag":               "Premium",
                "research_summary":   research_summary,
                "investment_opinion": investment_opinion,
                "investment_score": investment_score
            }
        except Exception as e:
            print(f"❌ Error al preparar payload para {company_name}: {e}")
            continue

    try:
        dest_table.create(payload)
        print(f"✅ {company_name} subido correctamente.")
    except Exception as e:
        print(f"❌ Error subiendo {company_name} a Airtable: {e}")
