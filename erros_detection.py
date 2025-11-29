import os
import json
import shutil
from dotenv import load_dotenv
from pyairtable import Api

# === Configuración ===
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID          = os.getenv("AIRTABLE_BASE_ID")
TABLE_ID         = os.getenv("AIRTABLE_RESEARCH_TABLE_ID")
VIEW_ID          = "viwm150UxtF8l5Dtj"  # view for Airtable lookups

# Carpetas
BASE_DIR           = os.path.dirname(__file__)
DIR_RESEARCH       = os.path.join(BASE_DIR, "Research Assistant")
DIR_BANKER         = os.path.join(BASE_DIR, "Private Banker")
DIR_ERROR          = os.path.join(DIR_RESEARCH, "error")
DIR_MISSING_INFO   = os.path.join(DIR_ERROR, "missing info")
DIR_PROCESS_ERROR  = os.path.join(DIR_ERROR, "process error")

# Crear carpetas
os.makedirs(DIR_MISSING_INFO, exist_ok=True)
os.makedirs(DIR_PROCESS_ERROR, exist_ok=True)

# Airtable
api   = Api(AIRTABLE_API_KEY)
table = api.base(BASE_ID).table(TABLE_ID)

# === Funciones ===
def is_missing_info(data):
    if not data.get("title") or not data.get("subtitle"):
        return True
    for ch in data.get("chapters", []):
        if not ch.get("title") or not ch.get("content"):
            return True
    return False

def has_process_error(data):
    keywords = [
        "Error generating content",
        "401 Client Error", "403 Client Error",
        "500 Server Error", "API Error",
        "Unauthorized", "Request failed"
    ]
    for ch in data.get("chapters", []):
        for key in keywords:
            if key in ch.get("content", ""):
                return True
    return False

def clean_company_name(raw):
    return raw.rstrip("_").replace("_", " ").strip()

def mark_airtable_error(company_name_cleaned):
    try:
        records = table.all(formula=f"{{company_name}} = '{company_name_cleaned}'")
        if not records:
            print(f"❌ No se encontró en Airtable: {company_name_cleaned}")
            return
        record_id = records[0]["id"]
        table.update(record_id, {"status": "ERROR"})
        print(f"🛠️ Airtable actualizado con status=ERROR para: {company_name_cleaned}")
    except Exception as e:
        print(f"❌ Error actualizando Airtable para {company_name_cleaned}: {e}")

# === MAIN ===
print(f"\n🔎 Analizando archivos JSON en: {DIR_RESEARCH}")
for fn in os.listdir(DIR_RESEARCH):
    if not fn.endswith("_Research.json"):
        continue

    research_path = os.path.join(DIR_RESEARCH, fn)

    try:
        with open(research_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo {fn}: {e}")
        continue

    base_name = fn.replace("_Research.json", "")
    company_name_cleaned = clean_company_name(base_name)

    dest_path = None
    if is_missing_info(data):
        dest_path = os.path.join(DIR_MISSING_INFO, fn)
    elif has_process_error(data):
        dest_path = os.path.join(DIR_PROCESS_ERROR, fn)

    if dest_path:
        shutil.move(research_path, dest_path)
        print(f"📁 {fn} movido a: {dest_path}")

        # Borrar archivo en Private Banker
        rec_fn = base_name + "_recommendation.json"
        rec_path = os.path.join(DIR_BANKER, rec_fn)
        if os.path.exists(rec_path):
            os.remove(rec_path)
            print(f"🗑️ Archivo eliminado de Private Banker: {rec_fn}")
        else:
            print(f"⚠️ No se encontró recomendación: {rec_fn}")

        # Marcar error en Airtable
        mark_airtable_error(company_name_cleaned)
    else:
        print(f"✅ {fn} está correcto.")

print("\n✅ Análisis de errores completado.")
