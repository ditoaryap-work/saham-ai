"""
fetch_data.py — Data Collector untuk saham-ai
Jalankan: python scripts/fetch_data.py
"""
import yfinance as yf
import pandas as pd
import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = "data/saham.db"
WATCHLIST_PATH = "config/watchlist.txt"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS harga (
        kode TEXT, tanggal TEXT, open REAL, high REAL, low REAL,
        close REAL, volume INTEGER, PRIMARY KEY (kode, tanggal))""")
    c.execute("""CREATE TABLE IF NOT EXISTS fundamental (
        kode TEXT PRIMARY KEY, per REAL, pbv REAL, roe REAL,
        market_cap REAL, div_yield REAL, updated TEXT)""")
    conn.commit()
    conn.close()

def load_watchlist():
    os.makedirs("config", exist_ok=True)
    if not os.path.exists(WATCHLIST_PATH):
        default = ["BBCA","BBRI","TLKM","ASII","GOTO","BREN","MDKA"]
        with open(WATCHLIST_PATH, "w") as f:
            f.write("\n".join(default))
    with open(WATCHLIST_PATH) as f:
        return [l.strip().upper() for l in f if l.strip()]

def fetch_and_store(kode: str):
    try:
        ticker = yf.Ticker(f"{kode}.JK")
        df = ticker.history(period="60d", interval="1d")
        df.index = df.index.tz_localize(None)

        conn = sqlite3.connect(DB_PATH)
        for date, row in df.iterrows():
            conn.execute("""INSERT OR REPLACE INTO harga
                VALUES (?,?,?,?,?,?,?)""",
                (kode, str(date.date()), row.Open, row.High,
                 row.Low, row.Close, int(row.Volume)))

        info = ticker.info
        conn.execute("""INSERT OR REPLACE INTO fundamental VALUES (?,?,?,?,?,?,?)""",
            (kode,
             info.get("trailingPE"),
             info.get("priceToBook"),
             info.get("returnOnEquity"),
             info.get("marketCap"),
             info.get("dividendYield"),
             datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"  ✓ {kode}")
    except Exception as e:
        print(f"  ✗ {kode}: {e}")

if __name__ == "__main__":
    print("=== Fetching data saham IDX ===")
    init_db()
    watchlist = load_watchlist()
    for kode in watchlist:
        fetch_and_store(kode)
    print("=== Selesai ===")
