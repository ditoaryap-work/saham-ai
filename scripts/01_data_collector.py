import yfinance as yf
import pandas as pd
import sqlite3
import requests
from datetime import datetime
import os
import sys
import time

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')
WATCHLIST_PATH = os.path.join(BASE_DIR, 'config', 'watchlist.txt')

# Konfigurasi GoAPI (Sumber Data Utama - Stabil & Tidak Di-Ban)
GOAPI_KEY = os.environ.get('GOAPI_KEY', 'a4e070be-3366-5e56-f513-6fd84794')
GOAPI_BASE = 'https://api.goapi.io/stock/idx'

# Konfigurasi YFinance (Sumber Cadangan)
yf.config.network.retries = 3

def setup_database():
    """Membuat tabel database jika belum ada."""
    print(f"[*] Menyiapkan database di: {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabel harga saham historis
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ohlcv (
        ticker TEXT,
        date DATE,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        PRIMARY KEY (ticker, date)
    )
    ''')
    conn.commit()
    conn.close()
    print("[+] Database siap.")

def get_watchlist():
    """Membaca daftar dari file watchlist.txt"""
    if not os.path.exists(WATCHLIST_PATH):
        print(f"[!] File watchlist tidak ditemukan di {WATCHLIST_PATH}. Membuat template...")
        os.makedirs(os.path.dirname(WATCHLIST_PATH), exist_ok=True)
        with open(WATCHLIST_PATH, 'w') as f:
            f.write("BBCA\nBBRI\nTLKM\nASII\nGOTO\nBREN\nMDKA\nADMR\nBMRI\nUNVR")
    
    with open(WATCHLIST_PATH, 'r') as f:
        tickers = [line.strip() for line in f.readlines() if line.strip()]
    return tickers


# ============================================================
# SUMBER 1: GoAPI (Utama - Stabil, Tidak pernah di-ban)
# ============================================================
def fetch_from_goapi(ticker):
    """Mengambil data historis 1 saham dari GoAPI."""
    url = f"{GOAPI_BASE}/{ticker}/historical"
    headers = {'X-API-KEY': GOAPI_KEY}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        
        data = r.json()
        if data.get('status') != 'success' or not data.get('data', {}).get('results'):
            return None
        
        results = data['data']['results']
        df = pd.DataFrame(results)
        
        # Standarisasi kolom
        df = df.rename(columns={
            'symbol': 'ticker',
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        df['ticker'] = ticker
        df = df[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']]
        return df
        
    except Exception as e:
        print(f"    [GoAPI Error] {ticker}: {e}")
        return None


# ============================================================
# SUMBER 2: Yahoo Finance / yfinance (Cadangan - Batch Mode)
# ============================================================
def fetch_from_yfinance(ticker_list, period="1y"):
    """Mengambil data dari yfinance secara batch. Digunakan sebagai fallback."""
    yf_tickers = [f"{t}.JK" for t in ticker_list]
    results = {}
    
    try:
        df_batch = yf.download(yf_tickers, period=period, group_by='ticker', threads=True)
        
        if df_batch.empty:
            return results
        
        for ticker in ticker_list:
            yf_symbol = f"{ticker}.JK"
            try:
                if len(ticker_list) > 1:
                    if yf_symbol not in df_batch.columns.levels[0]:
                        continue
                    df = df_batch[yf_symbol].copy()
                else:
                    df = df_batch[yf_symbol].copy() if yf_symbol in df_batch.columns.levels[0] else df_batch.copy()
            except Exception:
                continue

            df = df.dropna(how='all').reset_index()
            if df.empty:
                continue

            df.columns = [c.lower() for c in df.columns]
            date_col = 'date' if 'date' in df.columns else 'index'
            df[date_col] = pd.to_datetime(df[date_col]).dt.date
            df['ticker'] = ticker
            
            required_cols = ['ticker', date_col, 'open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]
            results[ticker] = df
            
    except Exception as e:
        print(f"  [YFinance Error] Batch download gagal: {e}")
    
    return results


# ============================================================
# FUNGSI UTAMA: Hybrid Fetch (GoAPI -> YFinance Fallback)
# ============================================================
def fetch_data(ticker_list, period="1y"):
    """
    Strategi Hybrid:
    1. Coba ambil dari GoAPI dulu (stabil, tidak pernah di-ban)
    2. Kumpulkan ticker yang gagal dari GoAPI
    3. Untuk ticker yang gagal, coba batch download via yfinance
    4. Gabungkan data dari database lama (jika ada) dengan data baru dari GoAPI
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"[*] Mulai mengambil data untuk {len(ticker_list)} saham (Hybrid: GoAPI + YFinance)...")
    
    goapi_success = []
    goapi_failed = []
    
    # === TAHAP 1: GoAPI (Sumber Utama) ===
    print("\n--- TAHAP 1: GoAPI (Sumber Utama) ---")
    for ticker in ticker_list:
        print(f"  -> [{ticker}] Mengunduh dari GoAPI...", end=" ")
        df = fetch_from_goapi(ticker)
        
        if df is not None and not df.empty:
            rows = [tuple(x) for x in df.to_numpy()]
            cursor.executemany('''
                INSERT OR REPLACE INTO ohlcv (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', rows)
            goapi_success.append(ticker)
            print(f"✅ ({len(df)} baris)")
        else:
            goapi_failed.append(ticker)
            print("❌ Gagal")
        
        time.sleep(1)  # Sopan terhadap GoAPI
    
    # === TAHAP 2: YFinance Fallback (Jika Ada yang Gagal) ===
    yf_success = []
    if goapi_failed:
        print(f"\n--- TAHAP 2: YFinance Fallback ({len(goapi_failed)} saham gagal dari GoAPI) ---")
        yf_results = fetch_from_yfinance(goapi_failed, period=period)
        
        for ticker, df in yf_results.items():
            if df is not None and not df.empty:
                rows = [tuple(x) for x in df.to_numpy()]
                cursor.executemany('''
                    INSERT OR REPLACE INTO ohlcv (ticker, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', rows)
                yf_success.append(ticker)
                print(f"  -> [{ticker}] ✅ YFinance berhasil ({len(df)} baris)")
    
    conn.commit()
    conn.close()
    
    # === TAHAP 3: Cek Data Existing di Database ===
    # Bahkan jika GoAPI & YFinance gagal, kita mungkin masih punya data lama di DB
    total_failed = [t for t in goapi_failed if t not in yf_success]
    
    if total_failed:
        conn2 = sqlite3.connect(DB_PATH)
        for ticker in total_failed:
            count = pd.read_sql_query(
                f"SELECT COUNT(*) as cnt FROM ohlcv WHERE ticker='{ticker}'", conn2
            )['cnt'].iloc[0]
            if count > 0:
                print(f"  -> [{ticker}] ⚠️ Sumber baru gagal, tapi masih ada {count} baris data lama di database.")
            else:
                print(f"  -> [{ticker}] ❌ GAGAL TOTAL. Tidak ada data sama sekali.")
        conn2.close()
    
    # === RINGKASAN ===
    print(f"\n{'='*50}")
    print(f"📊 RINGKASAN PENGUMPULAN DATA:")
    print(f"   GoAPI  Sukses : {len(goapi_success)} saham")
    print(f"   YFinance Sukses: {len(yf_success)} saham")
    print(f"   Gagal Total   : {len(total_failed)} saham")
    print(f"{'='*50}")
    print("[*] Selesai pengolahan data.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Saham AI Data Collector')
    parser.add_argument('--ticker', type=str, help='Ticker saham spesifik (opsional)')
    args = parser.parse_args()

    print(f"=== SAHAM AI DATA COLLECTOR ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    setup_database()
    
    if args.ticker:
        watchlist = [args.ticker.upper()]
    else:
        watchlist = get_watchlist()
        
    fetch_data(watchlist)
    print("=== SELESAI ===")
