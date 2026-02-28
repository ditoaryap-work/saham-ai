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
        'fundamental_score INTEGER', 'fundamental_status TEXT',
        'is_stale INTEGER DEFAULT 0'
    ]
    for col_def in new_columns:
        col_name = col_def.split()[0]
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE analisa_harian ADD COLUMN {col_def}")
            
    conn.commit()
    conn.close()

def get_cached_fundamental(ticker):
    """Mengambil data fundamental terakhir yang sukses dari database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"""
            SELECT pe_ratio, pbv_ratio, market_cap 
            FROM analisa_harian 
            WHERE ticker = '{ticker}' 
            AND pe_ratio > 0 
            ORDER BY date DESC LIMIT 1
        """
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            return df.iloc[0].to_dict()
    except:
        pass
    return None

def analyze_fundamental(ticker):
    """Mengambil dan menskor atribut fundamental emiten. Menggunakan fallback DB jika API Limit."""
    is_stale = 0
    try:
        yf_ticker = f"{ticker}.JK"
        stock = yf.Ticker(yf_ticker)
        
        # 1. Ambil Market Cap dari fast_info (Sangat ringan, anti-ban)
        try:
            market_cap = stock.fast_info.get('marketCap') or 0
        except Exception:
            market_cap = 0
            
        # 2. Ambil P/E dan PBV dari .info (Berat, sering kena 429)
        pe_ratio = 0.0
        pbv_ratio = 0.0
        
        try:
            info = stock.info
            pe_ratio = info.get('trailingPE') or 0.0
            pbv_ratio = info.get('priceToBook') or 0.0
        except Exception as e:
            if "Too Many Requests" in str(e) or market_cap == 0:
                print(f"    [!] {ticker}: Yahoo Rate Limit/Error. Mencoba ambil dari cache database...")
                cached = get_cached_fundamental(ticker)
                if cached:
                    pe_ratio = cached['pe_ratio']
                    pbv_ratio = cached['pbv_ratio']
                    market_cap = cached['market_cap'] if market_cap == 0 else market_cap
                    is_stale = 1
                    print(f"    [+] {ticker}: Menggunakan data fundamental cache (EOD Terakhir).")
                else:
                    print(f"    [!] {ticker}: Cache tidak tersedia. Menggunakan default 0.0.")
            else:
                print(f"    [!] {ticker}: Gagal mengambil data .info: {e}")
        
        score = 0
        # Rule 1: Valuasi Laba EPS (P/E Ratio)
        if 0 < pe_ratio < 20: 
            score += 2 # Murah dan menguntungkan
        elif pe_ratio >= 20: 
            score += 1 # Menguntungkan tapi premium
            
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
            status = "High Risk (Missing Data / Overvalued)"
            
        return {
            'ticker': ticker,
            'pe_ratio': pe_ratio,
            'pbv_ratio': pbv_ratio,
            'market_cap': market_cap,
            'fundamental_score': fund_score,
            'fundamental_status': status,
            'is_stale': is_stale
        }
    except Exception as e:
        print(f"  [X] Gagal total fetch data fundamental {ticker}: {e}")
        return None

def update_analysis(result):
    """Menyisipkan data fundamental ke SQLite, dicocokkan dengan ticker dan tanggal yang sama (hari ini)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE analisa_harian 
        SET pe_ratio=?, pbv_ratio=?, market_cap=?, fundamental_score=?, fundamental_status=?, is_stale=?, last_updated=CURRENT_TIMESTAMP
        WHERE ticker=? 
        AND date = (SELECT MAX(date) FROM analisa_harian WHERE ticker=?)
    ''', (
        result['pe_ratio'], result['pbv_ratio'], result['market_cap'], 
        result['fundamental_score'], result['fundamental_status'], result['is_stale'],
        result['ticker'], result['ticker']
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Saham AI Fundamental Filter')
    parser.add_argument('--ticker', type=str, help='Ticker saham spesifik (opsional)')
    args = parser.parse_args()

    print("=== SAHAM AI FUNDAMENTAL FILTER ===")
    setup_fundamental_columns()
    
    conn = sqlite3.connect(DB_PATH)
    if args.ticker:
        query = f"SELECT ticker FROM analisa_harian WHERE ticker = '{args.ticker.upper()}' GROUP BY ticker"
    else:
        query = "SELECT ticker FROM analisa_harian GROUP BY ticker"
        
    analyzed_tickers = pd.read_sql(query, conn)['ticker'].tolist()
    conn.close()
    
    if not analyzed_tickers:
        print("[*] Tidak ada ticker untuk dianalisa fundamental.")
    else:
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
