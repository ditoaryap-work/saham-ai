import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse
import ta
import numpy as np

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')
CHART_DIR = os.path.join(BASE_DIR, 'data', 'charts')

def get_data(ticker, days=60):
    """Mengambil data historis dari SQLite."""
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT date, open, high, low, close, volume FROM ohlcv WHERE ticker='{ticker}' ORDER BY date ASC"
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        return df
        
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df.tail(days)

def generate_chart(ticker):
    """Membuat chart teknikal (Price + EMA + RSI) dan menyimpannya sebagai PNG."""
    df = get_data(ticker)
    if df.empty or len(df) < 20:
        print(f"  [!] Data tidak cukup untuk membuat chart {ticker}.")
        return None

    # Hitung Indikator (Menggunakan lib 'ta')
    df['EMA13'] = ta.trend.EMAIndicator(df['close'], window=13).ema_indicator()
    df['EMA34'] = ta.trend.EMAIndicator(df['close'], window=34).ema_indicator()
    df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

    # Setup Plot (Dark Theme Aesthetic)
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    plt.subplots_adjust(hspace=0.3)

    # 1. Price vs EMA
    ax1.plot(df.index, df['close'], label='Close Price', color='#f0f0f0', linewidth=2, alpha=0.9)
    if df['EMA13'].notna().any():
        ax1.plot(df.index, df['EMA13'], label='EMA 13', color='#00ffcc', linewidth=1.5, linestyle='--')
    if df['EMA34'].notna().any():
        ax1.plot(df.index, df['EMA34'], label='EMA 34', color='#ff00ff', linewidth=1.5, linestyle='--')
    
    ax1.set_title(f"Technical Chart: {ticker}", fontsize=14, color='white', fontweight='bold')
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(alpha=0.2, linestyle=':')
    ax1.set_ylabel("Price (IDR)")

    # 2. RSI
    ax2.plot(df.index, df['RSI'], color='#ffcc00', linewidth=1.5)
    ax2.axhline(70, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax2.axhline(30, color='green', linestyle='--', alpha=0.5, linewidth=1)
    ax2.fill_between(df.index, 30, 70, color='#ffcc00', alpha=0.05)
    
    ax2.set_ylabel("RSI (14)")
    ax2.set_ylim(0, 100)
    ax2.grid(alpha=0.1)

    # Save
    os.makedirs(CHART_DIR, exist_ok=True)
    file_path = os.path.join(CHART_DIR, f"{ticker}.png")
    plt.savefig(file_path, dpi=120, bbox_inches='tight')
    plt.close()
    
    return file_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Saham AI Chart Generator')
    parser.add_argument('--ticker', type=str, required=True, help='Ticker saham spesifik')
    args = parser.parse_args()

    ticker = args.ticker.upper()
    print(f"=== SAHAM AI CHART GENERATOR ===")
    print(f"[*] Generating chart for: {ticker}")
    path = generate_chart(ticker)
    if path:
        print(f"  [+] Chart saved at: {path}")
    print("=== SELESAI ===")
