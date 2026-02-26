"""
run_all.py — Script utama yang dipanggil oleh n8n setiap pagi
Output: JSON ke stdout → dibaca oleh n8n
"""
import sys
import os
import json

# Tambahkan path scripts ke sys.path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from fetch_data import load_watchlist, fetch_and_store, init_db
from technical_analysis import analyze
from bandarmology import analyze_bandarmology
from fundamental_filter import filter_fundamental
from sentiment_scraper import collect_sentiment_data
from scoring_engine import hitung_skor, ranking

def run():
    init_db()
    watchlist = load_watchlist()
    print(f"Memproses {len(watchlist)} saham...", file=sys.stderr)

    results = []
    for kode in watchlist:
        try:
            # Fetch data terbaru
            fetch_and_store(kode)

            # Analisa per layer
            teknikal     = analyze(kode)
            fundamental  = filter_fundamental(kode)
            bandar       = analyze_bandarmology(kode, teknikal)
            sentiment_d  = collect_sentiment_data(kode)

            # Sentimen score sementara netral (akan di-score oleh LLM)
            sentimen_score = 1

            # Scoring final
            skor = hitung_skor(teknikal, bandar, fundamental, sentimen_score)
            skor["headlines"] = sentiment_d.get("headlines", [])
            results.append(skor)

            print(f"  ✓ {kode}: {skor['sinyal']} ({skor['skor']})", file=sys.stderr)
        except Exception as e:
            print(f"  ✗ {kode}: {e}", file=sys.stderr)

    # Ambil top 5
    top = ranking(results, top_n=5)
    print(json.dumps(top, ensure_ascii=False))

if __name__ == "__main__":
    run()
