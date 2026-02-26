# Skill: Data Collector
# Aktif saat: Membuat atau mengedit script pengambilan data saham IDX

## SUMBER DATA

| Sumber | Data | Library |
|---|---|---|
| Yahoo Finance (.JK) | OHLCV harga historis + intraday | yfinance |
| IDX API internal | Foreign flow, data emiten, keterbukaan | requests |
| Google News | Berita terkini per emiten | googlenews / feedparser |
| RSS Kontan/Bisnis | Berita ekonomi & korporasi | feedparser |

## WATCHLIST DEFAULT
Simpan di `config/watchlist.txt` — satu kode per baris (tanpa .JK).
Contoh: BBCA, BBRI, TLKM, ASII, GOTO, BREN, MDKA, ADMR

## STORAGE
- Gunakan SQLite (`data/saham.db`) untuk semua data historis
- Struktur tabel: `harga`, `fundamental`, `bandarmology`, `sentiment`, `sinyal`
- Jangan gunakan file CSV — tidak efisien untuk query lintas hari

## JADWAL FETCH
```
03.30 WIB  → fetch semua data (harga kemarin, berita 24 jam, fundamental)
Manual     → trigger via Telegram webhook kapan saja
```

## INSTALASI LIBRARY
```bash
pip install yfinance pandas pandas-ta requests feedparser python-telegram-bot schedule
```

## POLA FETCH DATA
```python
import yfinance as yf

def fetch_harga(kode: str, period: str = "60d", interval: str = "1d"):
    ticker = yf.Ticker(f"{kode}.JK")
    df = ticker.history(period=period, interval=interval)
    df.index = df.index.tz_localize(None)
    return df

def fetch_info_fundamental(kode: str):
    ticker = yf.Ticker(f"{kode}.JK")
    info = ticker.info
    return {
        "per":        info.get("trailingPE"),
        "pbv":        info.get("priceToBook"),
        "roe":        info.get("returnOnEquity"),
        "market_cap": info.get("marketCap"),
        "div_yield":  info.get("dividendYield"),
    }
```
