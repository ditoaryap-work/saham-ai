import sqlite3
import pandas as pd
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')
OUTPUT_JSON = os.path.join(BASE_DIR, 'data', 'llm_payload.json')

def prepare_llm_payload():
    """Mengambil saham dengan sinyal BUY hari ini dan mengemasnya menjadi JSON payload untuk n8n -> OpenRouter."""
    conn = sqlite3.connect(DB_PATH)
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
        print("[!] Tidak ada saham bersinyal BUY hari ini.")
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
                headlines = [h['title'] for h in headlines_json]
            else:
                headlines = ["Tidak ada berita signifikan 72 jam terakhir."]
        except:
            headlines = ["Tidak ada berita signifikan 72 jam terakhir."]

        signal_data = {
            "kode": f"{row['ticker']}",
            "tier": row['tier'],
            "keputusan_ai": row['final_decision'],
            "skor_akhir_sistem": int(row['final_score']),
            "harga_terakhir": float(row['close_price']),
            "stop_loss_rekomendasi": float(row['sl_price']),
            "take_profit_rekomendasi": float(row['tp1_price']),
            "kondisi_teknikal": row['trend_status'],
            "kondisi_macd": row['macd_signal'],
            "kondisi_bandarmologi": row['bandar_status'],
            "kondisi_fundamental": row['fundamental_status'],
            "berita_terbaru": headlines
        }
        signals.append(signal_data)
        
    system_prompt = """Kamu adalah Asisten AI Saham Profesional (Quant Trader) di Bursa Efek Indonesia (IHSG). 
Tugasmu adalah merangkum data objektif JSON berikut yang dihasilkan oleh algoritma Python, dan menuliskannya ulang menjadi pesan Telegram "Radar Saham / Morning Briefing" yang terstruktur, rapi, dan meyakinkan untuk seorang trader.
Gunakan emoticon yang sesuai. Jadikan analisisnya seakan-akan kamu adalah pakar pasar modal yang membaca data tersebut, tapi tetap ringkas. 
WAJIB menyorot indikasi penting seperti ledakan volume (akumulasi) atau kondisi jenuh jual (oversold). Dilarang menyarankan hold untuk saham Gorengan (Tier 3)."""
    
    payload = {
        "status": "success",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_signals": len(signals),
        "system_prompt": system_prompt,
        "raw_signals": signals
    }
    
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(payload, f, indent=4)
        
    print(f"[+] Laporan JSON LLM Payload berisikan {len(signals)} saham berhasil dibuat di:\n    -> {OUTPUT_JSON}")
    print("[+] File JSON ini siap dibaca oleh node N8N 'Read Binary File' untuk ditembakkan ke OpenRouter.")

if __name__ == "__main__":
    print(f"=== SAHAM AI LLM FORMATTER ===")
    prepare_llm_payload()
    print("=== SELESAI ===")
