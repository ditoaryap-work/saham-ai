import sqlite3
import pandas as pd
import yfinance as yf
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')

def setup_fundamental_columns():
    """Menambahkan kolom fundamental ke tabel analisa_harian jika belum ada."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Cek apakah kolom sudah ada
    cursor.execute("PRAGMA table_info(analisa_harian)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = [
        'pe_ratio REAL', 'pbv_ratio REAL', 'market_cap INTEGER', 
        'fundamental_score INTEGER', 'fundamental_status TEXT'
    ]
    for col_def in new_columns:
        col_name = col_def.split()[0]
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE analisa_harian ADD COLUMN {col_def}")
            
    conn.commit()
    conn.close()

def analyze_fundamental(ticker):
    """Mengambil dan menskor atribut fundamental emiten."""
    try:
        yf_ticker = f"{ticker}.JK"
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        
        # Seringkali yfinance mereturn None jika data tidak ada
        pe_ratio = info.get('trailingPE') or 0.0
        pbv_ratio = info.get('priceToBook') or 0.0
        market_cap = info.get('marketCap') or 0
        
        score = 0
        
        # Rule 1: Valuasi Laba EPS (P/E Ratio)
        if 0 < pe_ratio < 20: 
            score += 2 # Murah dan menguntungkan
        elif pe_ratio >= 20: 
            score += 1 # Menguntungkan tapi premium
        else:
            score += 0 # Rugi (P/E minus atau 0)
            
        # Rule 2: Valuasi Aset (PBV Ratio)
        if 0 < pbv_ratio < 3:
            score += 2 # Buku murah
        elif pbv_ratio >= 3:
            score += 1 # Buku premium (misal tech/bank)
            
        # Rule 3: Size & Likuiditas
        if market_cap > 10000000000000: # 10 Triliun Rupiah (Tier 1/2 safety net)
            score += 1
            
        # Normalisasi: Score maksimal 5 = 100
        fund_score = int((score / 5) * 100)
        
        if fund_score >= 80:
            status = "Sangat Sehat (Undervalued)"
        elif fund_score >= 40:
            status = "Standar"
        else:
            status = "High Risk (Overvalued/Rugi)"
            
        return {
            'ticker': ticker,
            'pe_ratio': pe_ratio,
            'pbv_ratio': pbv_ratio,
            'market_cap': market_cap,
            'fundamental_score': fund_score,
            'fundamental_status': status
        }
    except Exception as e:
        print(f"  [X] Gagal fetch data fundamental {ticker}: {e}")
        return None

def update_analysis(result):
    """Menyisipkan data fundamental ke SQLite, dicocokkan dengan ticker dan tanggal yang sama (hari ini)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE analisa_harian 
        SET pe_ratio=?, pbv_ratio=?, market_cap=?, fundamental_score=?, fundamental_status=?, last_updated=CURRENT_TIMESTAMP
        WHERE ticker=? 
        AND date = (SELECT MAX(date) FROM analisa_harian WHERE ticker=?)
    ''', (
        result['pe_ratio'], result['pbv_ratio'], result['market_cap'], 
        result['fundamental_score'], result['fundamental_status'],
        result['ticker'], result['ticker']
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("=== SAHAM AI FUNDAMENTAL FILTER ===")
    setup_fundamental_columns()
    
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT ticker FROM analisa_harian GROUP BY ticker"
    analyzed_tickers = pd.read_sql(query, conn)['ticker'].tolist()
    conn.close()
    
    print(f"[*] Mengambil data fundamental (P/E, PBV, Cap) untuk {len(analyzed_tickers)} saham...")
    
    for ticker in analyzed_tickers:
        print(f"  -> Menganalisa: {ticker}")
        fund_data = analyze_fundamental(ticker)
        if fund_data:
            update_analysis(fund_data)
            print(f"  [+] {ticker} : Skor Fundamental {fund_data['fundamental_score']} ({fund_data['fundamental_status']})")
        # Delay 1 detik untuk menghindari Rate Limit (429) dari server Yahoo API public
        time.sleep(1)
                
    print("=== SELESAI ===")
