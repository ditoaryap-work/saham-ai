"""
sentiment_scraper.py — Scrape berita & sentimen saham
"""
import feedparser
import json
from datetime import datetime, timedelta
import time

RSS_SOURCES = {
    "kontan": "https://feeds.feedburner.com/kontan/GXhb",
    "bisnis": "https://feeds.feedburner.com/BisniscomNews",
}

def get_google_news(kode: str, nama: str = "") -> list:
    query = f"{kode}+saham" + (f"+{nama.replace(' ', '+')}" if nama else "")
    url = f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    feed = feedparser.parse(url)
    cutoff = datetime.now() - timedelta(hours=24)
    berita = []
    for entry in feed.entries[:10]:
        berita.append(entry.get("title", ""))
    return berita

def get_rss_news(kode: str) -> list:
    berita = []
    for sumber, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                if kode.lower() in title.lower():
                    berita.append(title)
        except:
            pass
    return berita

def collect_sentiment_data(kode: str) -> dict:
    headlines = get_google_news(kode) + get_rss_news(kode)
    headlines = list(set(headlines))  # deduplikasi
    return {
        "kode": kode,
        "total_berita": len(headlines),
        "headlines": headlines[:10],  # maks 10 untuk hemat token LLM
    }

if __name__ == "__main__":
    result = collect_sentiment_data("BBCA")
    print(json.dumps(result, indent=2, ensure_ascii=False))
