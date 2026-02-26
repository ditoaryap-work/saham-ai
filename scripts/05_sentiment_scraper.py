import sqlite3
import pandas as pd
import feedparser
import os
import json
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'saham.db')

def setup_sentiment_columns():
    """Menambahkan kolom sentimen berita ke tabel analisa_harian jika belum ada."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(analisa_harian)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = ['news_sentiment_score INTEGER', 'news_headlines TEXT']
    for col_def in new_columns:
        col_name = col_def.split()[0]
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE analisa_harian ADD COLUMN {col_def}")
            
    conn.commit()
    conn.close()

def scrape_google_news(ticker, max_news=5):
    """Mengambil berita terbaru dari RSS Google News khusus kode saham IHSG."""
    query = f"{ticker} saham OR IDX"
    # URL encoded query
    query_encoded = query.replace(' ', '+')
    rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=id&gl=ID&ceid=ID:id"
    
    feed = feedparser.parse(rss_url)
    headlines = []
    
    # Ambil 72 jam terakhir (weekend filter)
    time_limit = datetime.now() - timedelta(hours=72)
    
    for entry in feed.entries:
        try:
            # Format sturct_time dari RSS diparse ke datetime python
            published_dt = datetime(*entry.published_parsed[:6])
            
            # Hanya ambil berita saham yang baru
            if published_dt >= time_limit:
                headlines.append({
                    "title": entry.title,
                    "date": published_dt.strftime("%Y-%m-%d %H:%M")
                })
        except:
            continue
            
        if len(headlines) >= max_news:
            break
            
    return headlines

def analyze_sentiment(ticker):
    """Membungkus headline dalam JSON. Nanti NLP IndoBERT yang skor, tapi sementara set skor 50 (Netral)."""
    headlines = scrape_google_news(ticker)
    
    # Default 50. LLM OpenRouter yang akan membaca JSON headlines ini dan menganalisanya nanti.
    score = 50 
    
    return {
        'ticker': ticker,
        'news_sentiment_score': score,
        'news_headlines': json.dumps(headlines, ensure_ascii=False)
    }

def update_analysis(result):
    """Update row terbaru di analisa_harian dengan berita."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE analisa_harian 
        SET news_sentiment_score=?, news_headlines=?, last_updated=CURRENT_TIMESTAMP
        WHERE ticker=? 
        AND date = (SELECT MAX(date) FROM analisa_harian WHERE ticker=?)
    ''', (
        result['news_sentiment_score'], result['news_headlines'],
        result['ticker'], result['ticker']
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("=== SAHAM AI SENTIMENT SCRAPER ===")
    setup_sentiment_columns()
    
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT ticker FROM analisa_harian GROUP BY ticker"
    analyzed_tickers = pd.read_sql(query, conn)['ticker'].tolist()
    conn.close()
    
    print(f"[*] Mengambil headline berita (RSS Google News) untuk {len(analyzed_tickers)} saham...")
    
    for ticker in analyzed_tickers:
        print(f"  -> Scraping berita: {ticker}")
        sent_data = analyze_sentiment(ticker)
        if sent_data:
            update_analysis(sent_data)
            headlines = json.loads(sent_data['news_headlines'])
            print(f"  [+] {ticker} : {len(headlines)} berita terkumpul. Skor Default: {sent_data['news_sentiment_score']}")
            for h in headlines:
                print(f"      - {h['title'][:80]}...")
                
    print("=== SELESAI ===")
