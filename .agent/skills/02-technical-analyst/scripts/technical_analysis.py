"""
technical_analysis.py — Kalkulasi indikator teknikal
"""
import pandas as pd
import pandas_ta as ta
import sqlite3
import json

DB_PATH = "data/saham.db"

def load_harga(kode: str, days: int = 60) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM harga WHERE kode=? ORDER BY tanggal DESC LIMIT ?",
        conn, params=(kode, days))
    conn.close()
    df = df.sort_values("tanggal").reset_index(drop=True)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df

def analyze(kode: str) -> dict:
    df = load_harga(kode)
    if len(df) < 30:
        return {"kode": kode, "error": "Data tidak cukup"}

    close = df["close"]
    volume = df["volume"]

    # Indikator
    rsi   = ta.rsi(close, length=14)
    macd  = ta.macd(close, fast=12, slow=26, signal=9)
    sma20 = ta.sma(close, length=20)
    sma50 = ta.sma(close, length=50)
    bb    = ta.bbands(close, length=20, std=2)
    atr   = ta.atr(df["high"], df["low"], close, length=14)

    rsi_val   = round(rsi.iloc[-1], 2)
    macd_line = round(macd["MACD_12_26_9"].iloc[-1], 4)
    macd_sig  = round(macd["MACDs_12_26_9"].iloc[-1], 4)
    macd_hist = round(macd["MACDh_12_26_9"].iloc[-1], 4)
    sma20_val = round(sma20.iloc[-1], 0)
    sma50_val = round(sma50.iloc[-1], 0)
    bb_low    = round(bb["BBL_20_2.0"].iloc[-1], 0)
    bb_mid    = round(bb["BBM_20_2.0"].iloc[-1], 0)
    bb_up     = round(bb["BBU_20_2.0"].iloc[-1], 0)
    atr_val   = atr.iloc[-1]
    harga     = close.iloc[-1]
    vol_ratio = round(volume.iloc[-1] / volume.iloc[-6:-1].mean(), 2)

    # Scoring
    score = 0
    if 30 < rsi_val < 60:                          score += 1
    if macd_line > macd_sig:                        score += 1
    if macd_hist > 0:                               score += 1
    if harga > sma20_val and harga > sma50_val:     score += 1
    if vol_ratio > 1.3:                             score += 1
    if bb_low < harga < bb_mid:                     score += 1

    # SL/TP
    sl  = round(harga - 1.5 * atr_val, 0)
    tp1 = round(harga + 2.0 * atr_val, 0)
    tp2 = round(harga + 3.5 * atr_val, 0)
    rr  = round((tp1 - harga) / max(harga - sl, 1), 2)

    return {
        "kode": kode,
        "harga": harga,
        "rsi": rsi_val,
        "macd": {"line": macd_line, "signal": macd_sig, "histogram": macd_hist},
        "sma": {"sma20": sma20_val, "sma50": sma50_val},
        "bb": {"low": bb_low, "mid": bb_mid, "up": bb_up},
        "volume_ratio": vol_ratio,
        "sl": sl, "tp1": tp1, "tp2": tp2, "rr": rr,
        "score_teknikal": score,
        "max_score": 6
    }

if __name__ == "__main__":
    from fetch_data import load_watchlist
    results = [analyze(k) for k in load_watchlist()]
    print(json.dumps(results, indent=2, default=str))
