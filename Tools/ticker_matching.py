import os
from dotenv import load_dotenv
from pyairtable import Api

# === Cargar variables de entorno ===
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# IDs de tablas
RESEARCH_TABLE_ID = "tblNfNES0Rt4K7oBV"
SYMBOL_TABLE_ID   = "tblnfIj6fZyKhtnkL"

# === Inicializar API ===
api = Api(AIRTABLE_API_KEY)
research_table = api.base(BASE_ID).table(RESEARCH_TABLE_ID)
symbol_table   = api.base(BASE_ID).table(SYMBOL_TABLE_ID)

# === Paso 1: Construir un diccionario de company_name -> symbol desde la tabla de símbolos ===
print("📥 Cargando tabla de símbolos...")
symbol_records = symbol_table.all()
symbol_map = {}

for record in symbol_records:
    fields = record.get("fields", {})
    company = fields.get("company_name", "").strip().lower()
    symbol  = fields.get("symbol", "").strip()
    if company and symbol:
        symbol_map[company] = symbol

# === Paso 2: Iterar por la tabla de Research y actualizar ticker si hace match con company_name ===
print("🔄 Actualizando tickers en la tabla de research...")
research_records = research_table.all()

for record in research_records:
    record_id = record["id"]
    fields    = record.get("fields", {})
    company   = fields.get("company_name", "").strip().lower()

    if not company:
        continue

    if company in symbol_map:
        current_ticker = fields.get("ticker", "").strip()
        new_ticker     = symbol_map[company]

        if current_ticker != new_ticker:
            try:
                research_table.update(record_id, {"ticker": new_ticker})
                print(f"✅ Actualizado: {company} → {new_ticker}")
            except Exception as e:
                print(f"❌ Error actualizando {company}: {e}")
    else:
        print(f"⚠️ No se encontró símbolo para: {company}")
