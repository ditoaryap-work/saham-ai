"""
scoring_engine.py — Gabungkan semua layer jadi skor final
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def hitung_skor(teknikal: dict, bandarmologi: dict, fundamental: dict, sentimen_score: int) -> dict:
    kode = teknikal["kode"]

    # Filter wajib
    if not fundamental.get("lulus", False):
        return {"kode": kode, "skor": 0, "sinyal": "❌ SKIP", "alasan": "Fundamental tidak lulus"}
    if teknikal.get("rr", 0) < 1.5:
        return {"kode": kode, "skor": 0, "sinyal": "❌ SKIP", "alasan": "Risk/Reward tidak memadai"}

    s_teknikal     = teknikal.get("score_teknikal", 0)
    s_bandar       = bandarmologi.get("score_bandarmologi", 0)
    s_fundamental  = fundamental.get("score_fundamental", 0)
    s_sentimen     = sentimen_score

    skor = (
        (s_teknikal / 6) * 30 +
        (s_bandar / 4) * 35 +
        (s_fundamental / 4) * 15 +
        (s_sentimen / 3) * 20
    )
    skor = round(skor, 1)

    if skor >= 70:   sinyal = "✅ STRONG BUY"
    elif skor >= 50: sinyal = "🟡 BUY"
    else:            sinyal = "❌ SKIP"

    return {
        "kode": kode,
        "skor": skor,
        "sinyal": sinyal,
        "harga": teknikal.get("harga"),
        "sl": teknikal.get("sl"),
        "tp1": teknikal.get("tp1"),
        "tp2": teknikal.get("tp2"),
        "rr": teknikal.get("rr"),
        "detail": {
            "teknikal": s_teknikal,
            "bandarmologi": s_bandar,
            "fundamental": s_fundamental,
            "sentimen": s_sentimen,
        }
    }

def ranking(results: list, top_n: int = 5) -> list:
    filtered = [r for r in results if r["sinyal"] != "❌ SKIP"]
    sorted_r = sorted(filtered, key=lambda x: x["skor"], reverse=True)
    return sorted_r[:top_n]

if __name__ == "__main__":
    # Contoh test
    dummy = hitung_skor(
        teknikal={"kode":"BBCA","harga":9850,"score_teknikal":5,"rr":2.1,"sl":9550,"tp1":10150,"tp2":10450},
        bandarmologi={"score_bandarmologi":3},
        fundamental={"score_fundamental":4,"lulus":True},
        sentimen_score=2
    )
    print(json.dumps(dummy, indent=2))
