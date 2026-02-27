import sqlite3
import pandas as pd
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')
OUTPUT_JSON = os.path.join(BASE_DIR, 'data', 'llm_payload.json')

def prepare_llm_payload(ticker_filter=None):
    """Mengambil saham dengan sinyal BUY hari ini dan mengemasnya menjadi JSON payload untuk n8n -> OpenRouter."""
    conn = sqlite3.connect(DB_PATH)
    
    if ticker_filter:
        # Untuk mode CEK: Abaikan filter sinyal BUY, tampilkan apapun hasilnya (Skip pun tampil)
        query = f"""
        SELECT * 
        FROM analisa_harian 
        WHERE ticker = '{ticker_filter.upper()}'
        AND date = (SELECT MAX(date) FROM analisa_harian WHERE ticker = '{ticker_filter.upper()}')
        """
    else:
        # Untuk mode RADAR: Hanya tampilkan yang Strong Buy atau Buy
        query = """
        SELECT * 
        FROM analisa_harian 
        WHERE date = (SELECT MAX(date) FROM analisa_harian)
        AND final_decision IN ('STRONG BUY', 'BUY (Swing/BSJP)')
        ORDER BY final_score DESC
        LIMIT 10
        """
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        print(f"[!] Tidak ada data untuk {'saham ' + ticker_filter if ticker_filter else 'sinyal BUY hari ini'}.")
        # Buat payload kosong agar N8N tidak error parsing
        with open(OUTPUT_JSON, 'w') as f:
            json.dump({"status": "no_signals", "data": []}, f)
        return

    # Siapkan raw text data analisis untuk OpenRouter
    signals = []
    
    for _, row in df.iterrows():
        # Parsing headlines json
        headlines = []
        try:
            if pd.notna(row['news_headlines']) and str(row['news_headlines']).strip() != "":
                headlines_json = json.loads(row['news_headlines'])
                for h in headlines_json:
                    headlines.append({
                        "judul": h.get("title", ""),
                        "tautan": h.get("link", "")
                    })
            else:
                headlines = [{"judul": "Tidak ada berita signifikan 72 jam terakhir.", "tautan": ""}]
        except:
            headlines = [{"judul": "Tidak ada berita signifikan 72 jam terakhir.", "tautan": ""}]

        signal_data = {
            "kode": f"{row['ticker']}",
            "tier": row['tier'],
            "keputusan_ai": row['final_decision'],
            "skor_akhir_sistem": int(row['final_score']),
            "harga_terakhir": float(row['close_price']),
            "area_support_terdekat": float(row['support_area']) if 'support_area' in row and pd.notna(row['support_area']) else 0.0,
            "area_resistance_terdekat": float(row['resistance_area']) if 'resistance_area' in row and pd.notna(row['resistance_area']) else 0.0,
            "stop_loss_rekomendasi": float(row['sl_price']),
            "take_profit_1": float(row['tp1_price']),
            "take_profit_2": float(row['tp2_price']) if 'tp2_price' in row and pd.notna(row['tp2_price']) else 0.0,
            "kondisi_teknikal": row['trend_status'],
            "kondisi_macd": row['macd_signal'],
            "kondisi_bandarmologi": row['bandar_status'],
            "kondisi_fundamental": row['fundamental_status'],
            "berita_terbaru": headlines
        }
        signals.append(signal_data)
        
    mode_text = f"Analisa Spesifik {ticker_filter.upper()}" if ticker_filter else "Radar Saham / Morning Briefing"
    
    system_prompt = f"""Kamu adalah Asisten AI Saham Profesional (Quant Trader) di Bursa Efek Indonesia (IHSG). 
Tugasmu adalah menganalisis data JSON dari algoritma Python dan merangkumnya menjadi pesan Telegram "{mode_text}".
ATURAN WAJIB (System Prompt V2):
1. BERSIKAP TEGAS & KRITIS. Jangan bertele-tele. Jika data buruk (Downtrend/Distribusi), katakan SKIP/JAUHI. Jika bagus, katakan BUY/HOLD.
2. Saat memberikan rekomendasi Buy/Sell, jelaskan MENGAPA harga referensinya di angka tersebut (Singgung angka Support/Resistance terdekat yang ada di data).
3. Berikan pencerahan matang terkait Target Take Profit 1 (Konservatif), Target Profit 2 (Optimis/Swing), dan Stop Loss yang ketat.
4. Lampirkan URL/Link asli berita dari data JSON jika ada (Gunakan format markdown `[Judul Berita](Link)`.
5. Gunakan format yang kaya (Banyak paragraf pendek, list, *bold*, emoticon 📈📉🎯💸) layaknya diskusi dengan mentor pasar modal.
6. Pantang keras menyarankan "Hold" atau "Buy" untuk saham GORENGAN (Tier 3) jika indikator bandar menunjukkan Distribusi."""
    
    payload = {
        "status": "success",
        "mode": "cek" if ticker_filter else "radar",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_signals": len(signals),
        "system_prompt": system_prompt,
        "raw_signals": signals
    }
    
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(payload, f, indent=4)
        
    print(f"[+] Laporan JSON LLM Payload berisikan {len(signals)} saham berhasil dibuat di:\n    -> {OUTPUT_JSON}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Saham AI LLM Formatter')
    parser.add_argument('--ticker', type=str, help='Ticker saham spesifik (opsional)')
    args = parser.parse_args()

    print(f"=== SAHAM AI LLM FORMATTER ===")
    prepare_llm_payload(args.ticker)
    print("=== SELESAI ===")
