import sqlite3
import pandas as pd
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')

def setup_final_score_columns():
    """Menambahkan kolom final score ke tabel analisa_harian."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(analisa_harian)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = ['final_score INTEGER', 'final_decision TEXT']
    for col_def in new_columns:
        col_name = col_def.split()[0]
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE analisa_harian ADD COLUMN {col_def}")
            
    conn.commit()
    conn.close()

def align_tiering(row):
    """Menentukan ulang TIER saham berdasarkan Market Cap dan Volume Transaksi."""
    market_cap = float(row.get('market_cap') or 0)
    close_price = float(row.get('close_price') or 0)
    volume_ratio = float(row.get('volume_spike_ratio') or 0)
    
    # Tier 1: Bluechip, Market Cap besar (> 20 T)
    if market_cap >= 20000000000000:
        return "Tier 1 (Bluechip)"
    # Tier 3: Gorengan, Market Cap kecil (< 2 T) ATAU volume spike gila > 3x
    elif market_cap < 2000000000000 or volume_ratio > 3.0:
        return "Tier 3 (Gorengan)"
    else:
        return "Tier 2 (Mid-Cap)"

def calculate_final_scores():
    """Menggabungkan 4 layer penilaian."""
    conn = sqlite3.connect(DB_PATH)
    # Ambil data hari/tanggal bursa terbaru (misal Jumat sore)
    query = """
    SELECT ticker, date, tech_score, bandar_score, fundamental_score, news_sentiment_score, tier, close_price, market_cap, volume_spike_ratio
    FROM analisa_harian 
    WHERE date = (SELECT MAX(date) FROM analisa_harian)
    """
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("[!] Tidak ada data untuk dianalisa hari ini.")
        conn.close()
        return

    # Bobot Default (Tek:30%, Ban:35%, Fund:15%, Sen:20%)
    w_tech = 0.30
    w_bandar = 0.35
    w_fund = 0.15
    w_sent = 0.20
    
    results = []
    
    for _, row in df.iterrows():
        try:
            ts = float(row['tech_score'] if pd.notna(row['tech_score']) else 0)
            bs = float(row['bandar_score'] if pd.notna(row['bandar_score']) else 0)
            fs = float(row['fundamental_score'] if pd.notna(row['fundamental_score']) else 0)
            ns = float(row['news_sentiment_score'] if pd.notna(row['news_sentiment_score']) else 0)
            
            # Dinamis ulang TIER
            actual_tier = align_tiering(row)
            
            # Penyesuaian Bobot Berdasarkan Tier
            if "3" in actual_tier:
                # Gorengan: Bandarmologi dan Teknikal Breakout jadi raja, Fundamental diabaikan
                w_t, w_b, w_f, w_s = 0.25, 0.55, 0.00, 0.20
            elif "1" in actual_tier:
                # Bluechip: Fundamental dan Bandar asing penting, teknikal agak santai
                w_t, w_b, w_f, w_s = 0.25, 0.35, 0.30, 0.10
            else:
                # Tier 2 Default: 
                w_t, w_b, w_f, w_s = w_tech, w_bandar, w_fund, w_sent

            final_score = (ts * w_t) + (bs * w_b) + (fs * w_f) + (ns * w_s)
            final_score = int(final_score)
            
            # Decision Tree
            if final_score >= 70:
                decision = "STRONG BUY"
            elif final_score >= 55:
                decision = "BUY (Swing/BSJP)"
            elif final_score >= 45:
                decision = "HOLD / WATCH"
            else:
                decision = "SKIP"
                
            results.append({
                'ticker': row['ticker'],
                'date': row['date'],
                'final_score': final_score,
                'final_decision': decision,
                'tier': actual_tier
            })
            print(f"  [+] {row['ticker']:<5} | TIER: {actual_tier[:6]} | Skor Akhir: {final_score:3d} => {decision}")
            
        except Exception as e:
            print(f"  [X] Gagal memproses {row['ticker']}: {e}")

    # Update DB
    cursor = conn.cursor()
    for res in results:
        cursor.execute('''
            UPDATE analisa_harian 
            SET final_score=?, final_decision=?, tier=?, last_updated=CURRENT_TIMESTAMP
            WHERE ticker=? AND date=?
        ''', (res['final_score'], res['final_decision'], res['tier'], res['ticker'], res['date']))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print(f"=== SAHAM AI SCORING ENGINE ===")
    setup_final_score_columns()
    print("[*] Menghitung skor akhir gabungan 4 layer dengan Multiple-Tier Weighting...")
    calculate_final_scores()
    print("=== SELESAI ===")
