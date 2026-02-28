import sqlite3
import pandas as pd
import ta
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')

def setup_analysis_table():
    """Membuat tabel untuk menyimpan hasil analisa teknikal hari ini."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analisa_harian (
        ticker TEXT PRIMARY KEY,
        date DATE,
        close_price REAL,
        trend_status TEXT,
        rsi_14 REAL,
        macd_signal TEXT,
        volume_spike_ratio REAL,
        atr_14 REAL,
        sl_price REAL,
        tp1_price REAL,
        tech_score INTEGER,
        tier TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Migrasi penambahan kolom baru untuk V2
    cursor.execute("PRAGMA table_info(analisa_harian)")
    columns = [row[1] for row in cursor.fetchall()]
    for col_def in ['tp2_price REAL', 'support_area REAL', 'resistance_area REAL']:
        col_name = col_def.split()[0]
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE analisa_harian ADD COLUMN {col_def}")
            
    conn.commit()
    conn.close()

def get_latest_data(ticker, days=100):
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

def analyze_technical(df):
    """Menghitung indikator teknikal kustom untuk Trading Pro."""
    if len(df) < 20:
        return None  # Datanya terlalu sedikit (GoAPI free memberikan 21 hari)
    
    # 1. Moving Averages (Trend Filter)
    df['EMA_13'] = ta.trend.ema_indicator(df['close'], window=13)
    df['EMA_34'] = ta.trend.ema_indicator(df['close'], window=34)
    df['EMA_89'] = ta.trend.ema_indicator(df['close'], window=89)
    
    # 2. RSI & Stochastic RSI (Rebound Hunter)
    df['RSI_14'] = ta.momentum.rsi(df['close'], window=14)
    stoch_rsi = ta.momentum.StochRSIIndicator(df['close'], window=14, smooth1=3, smooth2=3)
    df['STOCHRSIk_14_14_3_3'] = stoch_rsi.stochrsi_k()
    df['STOCHRSId_14_14_3_3'] = stoch_rsi.stochrsi_d()
    
    # 3. MACD
    macd_ind = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD_12_26_9'] = macd_ind.macd()
    df['MACDs_12_26_9'] = macd_ind.macd_signal()
    df['MACDh_12_26_9'] = macd_ind.macd_diff()
        
    # 4. Volatility & Stop Loss (ATR)
    df['ATR_14'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    
    # 5. Volume Spike Detection
    # Rata-rata volume 5 hari sebelumnya (tidak termasuk hari ini)
    df['Vol_MA5'] = df['volume'].shift(1).rolling(window=5).mean()
    df['Vol_Spike_Ratio'] = df['volume'] / df['Vol_MA5']
    
    return df

def generate_signals(ticker, df):
    """Menghasilkan skor dan sinyal berdasarkan data teknikal hari terakhir."""
    if df is None or len(df) < 2:
        return None
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    close = float(latest['close'])
    atr = float(latest['ATR_14'])
    
    # -- TIERING Sederhana --
    # Jika rata-rata transaksi harian > 50 Miliar = Tier 1 (Bluechip)
    # Jika rata-rata transaksi < 5 Miliar = Tier 3 (Gorengan)
    # Pendekatan: kita cek volume x close (estimasi Rupiah transaksi) kelak di Fundamenta_Filter.
    # Untuk sementara kita set default.
    tier = "Tier 2" 
    
    score = 0
    signals = []
    
    # 1. Trend Analysis (EMA 13, 34, 89)
    # Pastikan EMA_89 ada (butuh minimal 89 baris data)
    ema89_val = latest['EMA_89'] if 'EMA_89' in latest and pd.notna(latest['EMA_89']) else 0
    
    if close > latest['EMA_13'] > latest['EMA_34']:
        score += 2
        trend_status = "UPTREND (Strong)"
    elif close > latest['EMA_34']:
        score += 1
        trend_status = "UPTREND (Weak) / Rebound"
    else:
        trend_status = "DOWNTREND"
        
    # 2. MACD Crossover Signal
    macd_line_col = 'MACD_12_26_9'
    signal_line_col = 'MACDs_12_26_9'
    
    if latest[macd_line_col] > latest[signal_line_col] and prev[macd_line_col] <= prev[signal_line_col]:
        score += 2
        macd_signal = "Bullish Crossover"
    elif latest[macd_line_col] > latest[signal_line_col]:
        score += 1
        macd_signal = "Bullish"
    else:
        macd_signal = "Bearish"
        
    # 3. RSI Divergence / Oversold
    rsi = latest['RSI_14']
    if rsi < 35:
        score += 1  # Bonus oversold
        
    # 4. Volume Spike (Jejak Bandar)
    vol_ratio = latest['Vol_Spike_Ratio']
    if pd.notna(vol_ratio) and vol_ratio > 2.0 and close > prev['close']:
        score += 2 # Volume meledak dan harga naik (Akumulasi kuat)
        if vol_ratio > 3.0: tier = "Tier 3" # Kemungkinan digoreng dadakan
        
    # 5. Penetapan SL dan TP berbasis ATR (Standar Pro)
    sl_price = close - (1.5 * atr)
    tp1_price = close + (2.0 * atr)
    tp2_price = close + (3.5 * atr)
    support_area = close - (0.5 * atr)
    resistance_area = close + (1.0 * atr)
    
    # Normalisasi Skor (Misal Maks 7 poin di konversi ke skala 1-100 khusus teknikal porsi)
    # Namun karena ini hanya 1 Layer (Layer Teknikal), biarkan nilainya mentah atau max 100
    tech_score = int((score / 7) * 100)
    if tech_score > 100: tech_score = 100
    
    return {
        'ticker': ticker,
        'date': str(latest.name.date()),
        'close_price': close,
        'trend_status': trend_status,
        'rsi_14': rsi if pd.notna(rsi) else 0,
        'macd_signal': macd_signal,
        'volume_spike_ratio': vol_ratio if pd.notna(vol_ratio) else 0.0,
        'atr_14': atr if pd.notna(atr) else 0,
        'sl_price': sl_price,
        'support_area': support_area,
        'resistance_area': resistance_area,
        'tp1_price': tp1_price,
        'tp2_price': tp2_price,
        'tech_score': tech_score,
        'tier': tier
    }

def save_analysis(result):
    """Menyimpan hasil ke SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO analisa_harian 
        (ticker, date, close_price, trend_status, rsi_14, macd_signal, volume_spike_ratio, atr_14, sl_price, support_area, resistance_area, tp1_price, tp2_price, tech_score, tier, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        result['ticker'], result['date'], result['close_price'], result['trend_status'], 
        result['rsi_14'], result['macd_signal'], result['volume_spike_ratio'], 
        result['atr_14'], result['sl_price'], result['support_area'], result['resistance_area'],
        result['tp1_price'], result['tp2_price'], result['tech_score'], result['tier']
    ))
    conn.commit()
    conn.close()

def analyze_ticker(ticker):
    df = get_latest_data(ticker, days=120)
    df_ta = analyze_technical(df)
    if df_ta is not None:
        sig = generate_signals(ticker, df_ta)
        if sig:
            save_analysis(sig)
            print(f"  [+] {ticker} : Skor Teknikal {sig['tech_score']} ({sig['trend_status']})")
        else:
            print(f"  [-] {ticker} : Gagal generate signal.")
    else:
        print(f"  [-] {ticker} : Data tidak cukup untuk analisis.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Saham AI Technical Analyst')
    parser.add_argument('--ticker', type=str, help='Ticker saham spesifik (opsional)')
    args = parser.parse_args()

    print("=== SAHAM AI TECHNICAL ANALYST ===")
    setup_analysis_table()
    
    conn = sqlite3.connect(DB_PATH)
    if args.ticker:
        # Hanya ambil ticker spesifik yang ada di ohlcv
        query = f"SELECT DISTINCT ticker FROM ohlcv WHERE ticker = '{args.ticker.upper()}'"
    else:
        query = "SELECT DISTINCT ticker FROM ohlcv"
    
    tickers = pd.read_sql(query, conn)['ticker'].tolist()
    conn.close()
    
    if not tickers:
        if args.ticker:
            print(f"[*] Ticker '{args.ticker.upper()}' tidak ditemukan dalam database.")
        else:
            print("[*] Tidak ada ticker ditemukan dalam database.")
        print("=== SELESAI ===")
        sys.exit(0)
    
    print(f"[*] Menghitung indikator untuk {len(tickers)} saham...")
    
    for ticker in tickers:
        analyze_ticker(ticker)
        
    print("=== SELESAI ===")
