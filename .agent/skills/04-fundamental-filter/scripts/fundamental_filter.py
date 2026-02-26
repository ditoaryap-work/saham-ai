"""
fundamental_filter.py — Filter fundamental dari SQLite
"""
import sqlite3
import json

DB_PATH = "data/saham.db"

def filter_fundamental(kode: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT per, pbv, roe, market_cap FROM fundamental WHERE kode=?",
        (kode,)).fetchone()
    conn.close()

    if not row:
        return {"kode": kode, "score_fundamental": 0, "lulus": False, "catatan": "Data tidak ada"}

    per, pbv, roe, market_cap = row
    score = 0
    if per and per < 20:              score += 1
    if pbv and pbv < 3:               score += 1
    if roe and roe > 0.10:            score += 1
    if market_cap and market_cap > 1e12: score += 1

    return {
        "kode": kode,
        "per": per, "pbv": pbv, "roe": roe, "market_cap": market_cap,
        "score_fundamental": score,
        "max_score": 4,
        "lulus": score >= 2
    }

if __name__ == "__main__":
    from fetch_data import load_watchlist
    results = [filter_fundamental(k) for k in load_watchlist()]
    print(json.dumps(results, indent=2, default=str))
