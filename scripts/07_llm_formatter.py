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
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    for _, row in df.iterrows():
        # Cek apakah data stale (Tanggal di DB < Hari ini)
        analysis_date = str(row['date'])
        data_is_stale = analysis_date < today_str or row.get('is_stale') == 1
        
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
            "skor_akhir_sistem": int(row['final_score']) if pd.notna(row.get('final_score')) else 0,
            "harga_terakhir": float(row['close_price']),
            "area_support_terdekat": float(row['support_area']) if 'support_area' in row and pd.notna(row['support_area']) else 0.0,
            "area_resistance_terdekat": float(row['resistance_area']) if 'resistance_area' in row and pd.notna(row['resistance_area']) else 0.0,
            "stop_loss_rekomendasi": float(row['sl_price']),
            "take_profit_1": float(row['tp1_price']),
            "take_profit_2": float(row['tp2_price']) if 'tp2_price' in row and pd.notna(row['tp2_price']) else 0.0,
            "kondisi_teknikal": row['trend_status'],
            "kondisi_macd": row['macd_signal'],
            "kondisi_bandarmology": row['bandar_status'],
            "kondisi_fundamental": row['fundamental_status'],
            "berita_terbaru": headlines,
            "image_url": f"https://bot-saham.ditoaryap.my.id/charts/{row['ticker']}.png",
            "data_status": "STALE (Cached)" if data_is_stale else "LIVE (Updated)",
            "last_price_date": analysis_date
        }
        signals.append(signal_data)
        
    mode_text = f"Analisa Spesifik {ticker_filter.upper()}" if ticker_filter else "Radar Saham / Morning Briefing"
    
    system_prompt = f"""Kamu adalah Asisten AI Saham Profesional (Quant Trader) di Bursa Efek Indonesia (IHSG). 
Tugasmu adalah menganalisis data JSON dari algoritma Python dan merangkumnya menjadi pesan Telegram "{mode_text}".

ATURAN WAJIB (System Prompt V3 - Clean & Visual):
1. **Waspada Data Stale**: Jika data_status adalah "STALE (Cached)", kamu WAJIB menuliskan peringatan di baris paling atas: "🔴 **Peringatan: Data Belum Update (Menggunakan EOD {analysis_date})**".
2. **Dilarang Menampilkan URL Panjang**. Gunakan format Markdown Anchor Text: `[Sumber Berita](Link)`.
3. **Pesan Ringkas**. Gunakan separator garis (`----------------`). Max 2-3 paragraf per saham.
4. **Visual Chart**: Sebutkan bahwa "Grafik teknikal telah dilampirkan di bawah".
5. **Bandarmology**: Jelaskan status bandar disertai alasan lonjakan volumenya.
6. **Rekomendasi**: Berikan angka harga beli, TP1, TP2, dan SL dengan sangat jelas."""
    
    payload = {
        "status": "success",
        "mode": "cek" if ticker_filter else "radar",
        "date": today_str,
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
