"""
bandarmology.py — Analisa foreign flow + volume spike
"""
import requests
import sqlite3
import json
import pandas as pd

DB_PATH = "data/saham.db"

def get_foreign_flow(kode: str) -> dict:
    """Fetch foreign net buy/sell dari IDX."""
    try:
        url = f"https://idx.co.id/api/v1/stock-data/foreign-transaction?stockCode={kode}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        # Ambil data terbaru
        latest = data.get("data", [{}])[0] if data.get("data") else {}
        return {
            "foreign_buy":  latest.get("foreignBuy", 0),
            "foreign_sell": latest.get("foreignSell", 0),
            "foreign_net":  latest.get("foreignNet", 0),
        }
    except Exception:
        return {"foreign_buy": 0, "foreign_sell": 0, "foreign_net": 0}

def analyze_bandarmology(kode: str, teknikal: dict) -> dict:
    """Gabungkan foreign flow dengan analisa volume dari data teknikal."""
    foreign = get_foreign_flow(kode)
    vol_ratio = teknikal.get("volume_ratio", 1.0)
    harga_naik = teknikal.get("macd", {}).get("histogram", 0) > 0

    score = 0
    if foreign["foreign_net"] > 0:          score += 2
    if vol_ratio > 1.5:                      score += 1
    if harga_naik and vol_ratio > 1.2:       score += 1

    return {
        "kode": kode,
        "foreign_net": foreign["foreign_net"],
        "volume_ratio": vol_ratio,
        "score_bandarmology": score,
        "max_score": 4
    }

if __name__ == "__main__":
    print(json.dumps(analyze_bandarmology("BBCA", {"volume_ratio": 1.8, "macd": {"histogram": 0.5}}), indent=2))
