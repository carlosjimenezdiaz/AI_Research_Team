import os
from pyairtable import Table
from dotenv import load_dotenv
import yfinance as yf
from datetime import datetime

# === Load environment variables ===
load_dotenv()

# Airtable config
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_ID = os.getenv("AIRTABLE_RESEARCH_TABLE_ID")

# Airtable client
table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID)

# Start of current year
start_of_year = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')

# Fetch all records
records = table.all()

for record in records:
    fields = record.get("fields", {})
    ticker = fields.get("ticker")

    if not ticker:
        continue

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_of_year)
        info = stock.info  # Load metadata

        if hist.empty or len(hist["Close"]) < 2:
            print(f"No sufficient YTD data for {ticker}")
            continue

        start_price = hist["Close"].iloc[0]
        latest_price = hist["Close"].iloc[-1]

        ytd_dollar = round(latest_price - start_price, 2)
        ytd_percentage = round(((latest_price - start_price) / start_price) * 100, 2)
        last_closing_price = round(latest_price, 2)
        market_cap = info.get("marketCap", None)

        if market_cap:
            market_cap = round(market_cap, 2)

        # Update Airtable record (column name: "marketcap")
        table.update(record["id"], {
            "ytd_dollar": ytd_dollar,
            "ytd_percentage": ytd_percentage,
            "last_closing_price": last_closing_price,
            "marketcap": market_cap  # <-- aquí el cambio
        })

        print(f"✅ {ticker}: ${ytd_dollar}, {ytd_percentage}%, Close: ${last_closing_price}, Market Cap: ${market_cap}")

    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
