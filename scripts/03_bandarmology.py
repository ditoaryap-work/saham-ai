import sqlite3
import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')

def setup_bandar_columns():
    """Menambahkan kolom bandarmology ke tabel analisa_harian jika belum ada."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Cek apakah kolom sudah ada
    cursor.execute("PRAGMA table_info(analisa_harian)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = ['vwap REAL', 'obv REAL', 'bandar_score INTEGER', 'bandar_status TEXT']
    for col_def in new_columns:
        col_name = col_def.split()[0]
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE analisa_harian ADD COLUMN {col_def}")
            
    conn.commit()
    conn.close()

def get_latest_data(ticker, days=30):
    """Mengambil n hari terakhir data per saham dari SQLite."""
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT date, open, high, low, close, volume FROM ohlcv WHERE ticker='{ticker}' ORDER BY date ASC"
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        return df
        
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df.tail(days)

def analyze_bandarmology(df):
    """Menghitung Jejak Bandar menggunakan data OHLCV via VWAP dan OBV."""
    if len(df) < 20: 
        return None
        
    # 1. Hitung Typical Price
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    
    # 2. Hitung harian VWAP (Volume Weighted Average Price) untuk periode tertentu
    # Karena data harian, kita menggunakan Anchor VWAP atau rolling VWAP 5 hari
    df['VP'] = df['Typical_Price'] * df['volume']
    df['Rolling_Vol'] = df['volume'].rolling(window=5).sum()
    df['Rolling_VP'] = df['VP'].rolling(window=5).sum()
    df['VWAP_5d'] = df['Rolling_VP'] / df['Rolling_Vol']
    
    # 3. Hitung OBV (On-Balance Volume)
    # OBV naik jika daily close > yesterday close, turun jika sebaliknya
    obv = [0]
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['close'].iloc[i-1]:
            obv.append(obv[-1] + df['volume'].iloc[i])
        elif df['close'].iloc[i] < df['close'].iloc[i-1]:
            obv.append(obv[-1] - df['volume'].iloc[i])
        else:
            obv.append(obv[-1])
            
    df['OBV'] = obv
    df['OBV_MA9'] = df['OBV'].rolling(window=9).mean()
    
    return df

def generate_bandar_signals(ticker, df):
    """Membuat keputusan score akumulasi / distribusi dari jejak bandar volume."""
    if df is None or len(df) < 5:
        return None
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    close = float(latest['close'])
    vwap = float(latest['VWAP_5d'])
    
    score = 0
    
    # Rule 1: Harga vs VWAP
    # Jika harga close di atas nilai rata-rata VWAP 5 hari, indikasi bandar sedang tarik ke atas
    if close > vwap:
        score += 2
        bandar_status = "Akumulasi"
    else:
        bandar_status = "Distribusi / Mark Down"
        
    # Rule 2: OBV Trend
    if latest['OBV'] > latest['OBV_MA9']:
        score += 2
    
    # Normalisasi ke skala 0-100 untuk porsi Bandarmology
    bandar_score = int((score / 4) * 100)
    
    # Koreksi status jika divergence
    if close > vwap and latest['OBV'] < latest['OBV_MA9']:
        bandar_status = "Fake Breakout (Hati-hati)"
    elif close < vwap and latest['OBV'] > latest['OBV_MA9']:
        bandar_status = "Hidden Accumulation"
        
    return {
        'ticker': ticker,
        'date': str(latest.name.date()),
        'vwap': vwap if pd.notna(vwap) else 0.0,
        'obv': latest['OBV'],
        'bandar_score': bandar_score,
        'bandar_status': bandar_status
    }

def update_analysis(result):
    """Update tabel analisa_harian."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE analisa_harian 
        SET vwap=?, obv=?, bandar_score=?, bandar_status=?, last_updated=CURRENT_TIMESTAMP
        WHERE ticker=? AND date=?
    ''', (
        result['vwap'], result['obv'], result['bandar_score'], result['bandar_status'],
        result['ticker'], result['date']
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Saham AI Bandarmology Analyst')
    parser.add_argument('--ticker', type=str, help='Ticker saham spesifik (opsional)')
    args = parser.parse_args()

    print("=== SAHAM AI BANDARMOLOGY ANALYST ===")
    setup_bandar_columns()
    
    conn = sqlite3.connect(DB_PATH)
    if args.ticker:
        query = f"SELECT ticker, MAX(date) as max_date FROM analisa_harian WHERE ticker = '{args.ticker.upper()}' GROUP BY ticker"
    else:
        query = "SELECT ticker, MAX(date) as max_date FROM analisa_harian GROUP BY ticker"
        
    analyzed_tickers = pd.read_sql(query, conn)['ticker'].tolist()
    conn.close()
    
    if not analyzed_tickers:
        print("[*] Tidak ada ticker untuk dianalisa bandarmology.")
        sys.exit(0)

    print(f"[*] Menghitung jejak bandar (VWAP & OBV) untuk {len(analyzed_tickers)} saham...")
    
    for ticker in analyzed_tickers:
        df = get_latest_data(ticker, days=30)
        df_bandar = analyze_bandarmology(df)
        if df_bandar is not None:
            sig = generate_bandar_signals(ticker, df_bandar)
            if sig:
                update_analysis(sig)
                print(f"  [+] {ticker} : Skor Bandar {sig['bandar_score']} ({sig['bandar_status']})")
                
    print("=== SELESAI ===")
