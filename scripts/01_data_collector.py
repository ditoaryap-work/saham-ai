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

# Konfigurasi YFinance dari dokumentasi resmi (ranaroussi.github.io)
# Mengaktifkan auto-retry dengan exponential backoff untuk menembus limit ringan
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
        # Hapus spasi kosong dan baris kosong
        tickers = [line.strip() for line in f.readlines() if line.strip()]
    return tickers

def fetch_data(ticker_list, period="1y"):
    """Mengambil data dari yfinance secara batch lalu memasukkannya ke DB SQLite"""
    conn = sqlite3.connect(DB_PATH)
    
    # Format tickers untuk Yahoo Finance (.JK)
    yf_tickers = [f"{t}.JK" for t in ticker_list]
    
    print(f"[*] Mulai mengambil data untuk {len(ticker_list)} saham secara BATCH...")
    
    try:
        # Menggunakan yf.download sesuai anuran dokumentasi resmi (Multi-threading aktif secara default)
        # group_by='ticker' memastikan struktur data konsisten (Ticker -> Price)
        df_batch = yf.download(yf_tickers, period=period, group_by='ticker', threads=True)
        
        if df_batch.empty:
            print("[!] Gagal mengunduh data atau data kosong.")
            return

        cursor = conn.cursor()
        
        for ticker in ticker_list:
            yf_symbol = f"{ticker}.JK"
            
            # Mendukung baik hasil MultiIndex (banyak ticker) maupun Single (1 ticker)
            try:
                if len(ticker_list) > 1:
                    if yf_symbol not in df_batch.columns.levels[0]:
                        continue
                    df = df_batch[yf_symbol].copy()
                else:
                    # Untuk 1 ticker, yfinance mengembalikan DataFrame langsung jika bukan MultiIndex
                    # Tapi dengan group_by='ticker' dia tetap MultiIndex
                    df = df_batch[yf_symbol].copy() if yf_symbol in df_batch.columns.levels[0] else df_batch.copy()
            except Exception:
                print(f"  [!] Gagal mengambil slice data untuk {ticker}. Lewati.")
                continue

            # Bersihkan baris yang kosong (misal bursa tutup)
            df = df.dropna(how='all').reset_index()
            
            if df.empty:
                print(f"  [!] Data {ticker} kosong setelah pembersihan. Lewati.")
                continue

            # Standarisasi kolom (lowercase)
            df.columns = [c.lower() for c in df.columns]
            
            # Format tanggal (hapus info jam/timezone)
            # Kolom index biasanya bernama 'Date' atau 'date'
            date_col = 'date' if 'date' in df.columns else 'index'
            df[date_col] = pd.to_datetime(df[date_col]).dt.date
            df['ticker'] = ticker
            
            # Pilih & Urutkan kolom sesuai tabel SQLite
            required_cols = ['ticker', date_col, 'open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]
            
            # Simpan ke SQLite (UPSERT)
            rows = [tuple(x) for x in df.to_numpy()]
            cursor.executemany('''
                INSERT OR REPLACE INTO ohlcv (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', rows)
            
            print(f"  [+] Berhasil menyimpan {len(df)} baris data {ticker}.")

        conn.commit()
    except Exception as e:
        print(f"[X] Terjadi kesalahan fatal saat batch download: {e}")
    finally:
        conn.close()
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
