import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
import os
import sys
import time

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')
WATCHLIST_PATH = os.path.join(BASE_DIR, 'config', 'watchlist.txt')

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
        # Hapus spasi kosong dan baris kosong
        tickers = [line.strip() for line in f.readlines() if line.strip()]
    return tickers

def fetch_data(ticker_list, period="1y"):
    """Mengambil data dari yfinance lalu memasukkannya ke DB SQLite"""
    conn = sqlite3.connect(DB_PATH)
    
    print(f"[*] Mulai mengambil data untuk {len(ticker_list)} saham...")
    
    for ticker in ticker_list:
        # Di yfinance, saham IHSG diakhiri dengan .JK
        yf_ticker = f"{ticker}.JK"
        print(f"  -> Mengunduh: {yf_ticker}")
        
        try:
            # Memanipulasi session request untuk mengecoh anti-bot Yahoo
            session = yf.utils.get_tz_cache().session
            if session:
                session.headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            
            stock = yf.Ticker(yf_ticker)
            # Ambil data historis (default 1 tahun, berguna untuk moving average panjang)
            df = stock.history(period=period)
            
            if df.empty:
                print(f"  [!] Data {yf_ticker} kosong. Lewati.")
                time.sleep(1) # Delay kecil untuk aman
                continue
            
            # Reset index agar Date menjadi kolom biasa
            df = df.reset_index()
            
            # Ekstrak tanggal (hapus info timezone jika ada agar rapi di SQLite)
            df['Date'] = df['Date'].dt.date
            df['ticker'] = ticker
            
            # Pilih kolom yang kita butuhkan saja
            df = df[['ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            # Ubah nama kolom agar cocok dengan SQLite (lowercase)
            df.columns = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
            
            # Simpan ke SQLite (replace records existing with same primary key)
            # Metode "to_sql" default tidak punya operasi UPSERT (ON CONFLICT REPLACE)
            # Jadi kita lakukan insert dengan query SQLite
            cursor = conn.cursor()
            rows = [tuple(x) for x in df.to_numpy()]
            
            cursor.executemany('''
                INSERT OR REPLACE INTO ohlcv (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', rows)
            
            conn.commit()
            print(f"  [+] Berhasil menyimpan {len(df)} baris data {ticker}.")
            
            # Memberikan napas pada API Yahoo agar IP tidak diban
            time.sleep(2)
            
        except Exception as e:
            print(f"  [X] Gagal memproses {ticker}: {e}")
            time.sleep(5) # Hukuman delay jika terkena rate limit
            
    conn.close()
    print("[*] Selesai mengumpulkan data.")

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
