#!/bin/bash
# =============================================================
#  ANTIGRAVITY SKILLS SETUP — saham-ai
#  Bot Sinyal Saham IDX — 4 Layer Analysis
#  Jalankan di root folder workspace: bash setup-skills.sh
# =============================================================
set -e
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
BASE=".agent/skills"
mkdir -p "$BASE"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ANTIGRAVITY SKILLS — saham-ai                      ║"
echo "║   IDX Stock Signal Bot · 9 Skills                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 00 — VALIDATION FLOW
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[1/9] 00-validation-flow...${NC}"
mkdir -p "$BASE/00-validation-flow"
cat > "$BASE/00-validation-flow/SKILL.md" << 'SKILL'
# AGENT RULES — saham-ai

## ATURAN UTAMA
Sebelum mengerjakan apapun, AI WAJIB:
1. Rangkum pemahaman atas permintaan secara singkat
2. Tampilkan konfirmasi berikut dan BERHENTI menunggu jawaban:

```
Apakah pemahaman saya sudah benar?
✅ Lanjut
✏️  Koreksi
```

Jika koreksi → ulangi dari awal.
Jika ambigu → tanyakan dulu sebelum merangkum.
**Tidak ada eksekusi tanpa konfirmasi.**
SKILL
echo -e "${GREEN}  ✓ 00-validation-flow${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 01 — DATA COLLECTOR
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[2/9] 01-data-collector...${NC}"
mkdir -p "$BASE/01-data-collector/scripts"
cat > "$BASE/01-data-collector/SKILL.md" << 'SKILL'
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
SKILL

cat > "$BASE/01-data-collector/scripts/fetch_data.py" << 'PYEOF'
"""
fetch_data.py — Data Collector untuk saham-ai
Jalankan: python scripts/fetch_data.py
"""
import yfinance as yf
import pandas as pd
import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = "data/saham.db"
WATCHLIST_PATH = "config/watchlist.txt"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS harga (
        kode TEXT, tanggal TEXT, open REAL, high REAL, low REAL,
        close REAL, volume INTEGER, PRIMARY KEY (kode, tanggal))""")
    c.execute("""CREATE TABLE IF NOT EXISTS fundamental (
        kode TEXT PRIMARY KEY, per REAL, pbv REAL, roe REAL,
        market_cap REAL, div_yield REAL, updated TEXT)""")
    conn.commit()
    conn.close()

def load_watchlist():
    os.makedirs("config", exist_ok=True)
    if not os.path.exists(WATCHLIST_PATH):
        default = ["BBCA","BBRI","TLKM","ASII","GOTO","BREN","MDKA"]
        with open(WATCHLIST_PATH, "w") as f:
            f.write("\n".join(default))
    with open(WATCHLIST_PATH) as f:
        return [l.strip().upper() for l in f if l.strip()]

def fetch_and_store(kode: str):
    try:
        ticker = yf.Ticker(f"{kode}.JK")
        df = ticker.history(period="60d", interval="1d")
        df.index = df.index.tz_localize(None)

        conn = sqlite3.connect(DB_PATH)
        for date, row in df.iterrows():
            conn.execute("""INSERT OR REPLACE INTO harga
                VALUES (?,?,?,?,?,?,?)""",
                (kode, str(date.date()), row.Open, row.High,
                 row.Low, row.Close, int(row.Volume)))

        info = ticker.info
        conn.execute("""INSERT OR REPLACE INTO fundamental VALUES (?,?,?,?,?,?,?)""",
            (kode,
             info.get("trailingPE"),
             info.get("priceToBook"),
             info.get("returnOnEquity"),
             info.get("marketCap"),
             info.get("dividendYield"),
             datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"  ✓ {kode}")
    except Exception as e:
        print(f"  ✗ {kode}: {e}")

if __name__ == "__main__":
    print("=== Fetching data saham IDX ===")
    init_db()
    watchlist = load_watchlist()
    for kode in watchlist:
        fetch_and_store(kode)
    print("=== Selesai ===")
PYEOF
echo -e "${GREEN}  ✓ 01-data-collector${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 02 — TECHNICAL ANALYST
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/9] 02-technical-analyst...${NC}"
mkdir -p "$BASE/02-technical-analyst/scripts"
cat > "$BASE/02-technical-analyst/SKILL.md" << 'SKILL'
# Skill: Technical Analyst
# Aktif saat: Membuat atau mengedit script kalkulasi indikator teknikal

## INDIKATOR YANG DIHITUNG

| Indikator | Parameter | Fungsi |
|---|---|---|
| RSI | 14 | Momentum, overbought/oversold |
| MACD | 12,26,9 | Tren + crossover sinyal |
| SMA | 20, 50, 200 | Arah tren jangka pendek/menengah/panjang |
| EMA | 9, 21 | Entry point yang responsif |
| Bollinger Bands | 20, 2 | Volatilitas + potensi breakout |
| Stochastic | 14, 3 | Konfirmasi entry |
| ATR | 14 | Kalkulasi SL/TP otomatis |
| Volume Ratio | 5d avg | Konfirmasi kekuatan sinyal |

## INTERPRETASI SINYAL

### RSI(14)
- < 30 → Oversold → potensi reversal naik
- 30–45 → Recovery zone → entry aman
- 45–60 → Netral → tren sedang
- > 70 → Overbought → hindari buy baru

### MACD
- MACD line cross above signal → Bullish
- Histogram berturut naik → momentum menguat
- Divergence bullish → potensi reversal kuat

### Volume Ratio
- > 1.5x rata-rata 5 hari → konfirmasi kuat
- < 0.7x → sinyal lemah, skip saham ini

## KALKULASI SL/TP OTOMATIS
```python
atr = df["ATR"].iloc[-1]
harga = df["Close"].iloc[-1]
stop_loss   = round(harga - (1.5 * atr), 0)
take_profit1 = round(harga + (2.0 * atr), 0)
take_profit2 = round(harga + (3.5 * atr), 0)
rr_ratio = (take_profit1 - harga) / (harga - stop_loss)
# Hanya rekomendasikan jika rr_ratio >= 1.5
```

## SCORING TEKNIKAL (maks 6 poin)
```python
score = 0
if 30 < rsi < 60:                          score += 1
if macd_line > signal_line:                score += 1
if macd_histogram > 0:                     score += 1
if close > sma20 and close > sma50:        score += 1
if volume_ratio > 1.3:                     score += 1
if lower_bb < close < middle_bb:           score += 1  # di zona beli BB
```
SKILL

cat > "$BASE/02-technical-analyst/scripts/technical_analysis.py" << 'PYEOF'
"""
technical_analysis.py — Kalkulasi indikator teknikal
"""
import pandas as pd
import pandas_ta as ta
import sqlite3
import json

DB_PATH = "data/saham.db"

def load_harga(kode: str, days: int = 60) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM harga WHERE kode=? ORDER BY tanggal DESC LIMIT ?",
        conn, params=(kode, days))
    conn.close()
    df = df.sort_values("tanggal").reset_index(drop=True)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df

def analyze(kode: str) -> dict:
    df = load_harga(kode)
    if len(df) < 30:
        return {"kode": kode, "error": "Data tidak cukup"}

    close = df["close"]
    volume = df["volume"]

    # Indikator
    rsi   = ta.rsi(close, length=14)
    macd  = ta.macd(close, fast=12, slow=26, signal=9)
    sma20 = ta.sma(close, length=20)
    sma50 = ta.sma(close, length=50)
    bb    = ta.bbands(close, length=20, std=2)
    atr   = ta.atr(df["high"], df["low"], close, length=14)

    rsi_val   = round(rsi.iloc[-1], 2)
    macd_line = round(macd["MACD_12_26_9"].iloc[-1], 4)
    macd_sig  = round(macd["MACDs_12_26_9"].iloc[-1], 4)
    macd_hist = round(macd["MACDh_12_26_9"].iloc[-1], 4)
    sma20_val = round(sma20.iloc[-1], 0)
    sma50_val = round(sma50.iloc[-1], 0)
    bb_low    = round(bb["BBL_20_2.0"].iloc[-1], 0)
    bb_mid    = round(bb["BBM_20_2.0"].iloc[-1], 0)
    bb_up     = round(bb["BBU_20_2.0"].iloc[-1], 0)
    atr_val   = atr.iloc[-1]
    harga     = close.iloc[-1]
    vol_ratio = round(volume.iloc[-1] / volume.iloc[-6:-1].mean(), 2)

    # Scoring
    score = 0
    if 30 < rsi_val < 60:                          score += 1
    if macd_line > macd_sig:                        score += 1
    if macd_hist > 0:                               score += 1
    if harga > sma20_val and harga > sma50_val:     score += 1
    if vol_ratio > 1.3:                             score += 1
    if bb_low < harga < bb_mid:                     score += 1

    # SL/TP
    sl  = round(harga - 1.5 * atr_val, 0)
    tp1 = round(harga + 2.0 * atr_val, 0)
    tp2 = round(harga + 3.5 * atr_val, 0)
    rr  = round((tp1 - harga) / max(harga - sl, 1), 2)

    return {
        "kode": kode,
        "harga": harga,
        "rsi": rsi_val,
        "macd": {"line": macd_line, "signal": macd_sig, "histogram": macd_hist},
        "sma": {"sma20": sma20_val, "sma50": sma50_val},
        "bb": {"low": bb_low, "mid": bb_mid, "up": bb_up},
        "volume_ratio": vol_ratio,
        "sl": sl, "tp1": tp1, "tp2": tp2, "rr": rr,
        "score_teknikal": score,
        "max_score": 6
    }

if __name__ == "__main__":
    from fetch_data import load_watchlist
    results = [analyze(k) for k in load_watchlist()]
    print(json.dumps(results, indent=2, default=str))
PYEOF
echo -e "${GREEN}  ✓ 02-technical-analyst${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 03 — BANDARMOLOGY
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[4/9] 03-bandarmology...${NC}"
mkdir -p "$BASE/03-bandarmology/scripts"
cat > "$BASE/03-bandarmology/SKILL.md" << 'SKILL'
# Skill: Bandarmology Analyst
# Aktif saat: Membuat atau mengedit script analisa pergerakan bandar

## KONSEP DASAR

Bandarmologi menganalisa siapa yang "bermain" di saham tersebut:
- **Foreign Flow** — dana asing net buy = sinyal kuat
- **Volume Spike** — lonjakan volume tidak wajar = bandar masuk
- **Price-Volume Divergence** — harga turun tapi volume naik = akumulasi diam-diam
- **Broker Dominance** — jika bisa diakses, broker mana yang paling banyak beli

## SUMBER DATA GRATIS

### Foreign Flow (dari IDX)
```python
# Endpoint IDX untuk data foreign transaction
IDX_FOREIGN_URL = "https://idx.co.id/api/v1/stock-data/foreign-transaction"
# Data: foreign_buy, foreign_sell, foreign_net per saham per hari
# Fetch setelah market close (16.30 WIB)
```

### Volume Spike Detection
Dihitung sendiri dari data yfinance — tidak perlu sumber eksternal.

## SCORING BANDARMOLOGY (maks 4 poin)
```python
score = 0
if foreign_net > 0:                           score += 2  # bobot tinggi
if volume_ratio > 1.5:                        score += 1
if harga_naik and volume_naik:                score += 1  # konfirmasi akumulasi
# Bonus: jika foreign_net > 5x rata-rata 5 hari → score += 1 (maks jadi 5)
```

## CATATAN PENTING
Data broker summary detail (siapa broker yang beli) hanya tersedia di
Stockbit Pro (Rp 200rb/bulan). Jika ingin akurasi bandarmologi lebih tinggi,
ini adalah investasi yang sangat direkomendasikan.
SKILL

cat > "$BASE/03-bandarmology/scripts/bandarmology.py" << 'PYEOF'
"""
bandarmology.py — Analisa foreign flow + volume spike
"""
import requests
import sqlite3
import json
import pandas as pd

DB_PATH = "data/saham.db"

def get_foreign_flow(kode: str) -> dict:
    """Fetch foreign net buy/sell dari IDX."""
    try:
        url = f"https://idx.co.id/api/v1/stock-data/foreign-transaction?stockCode={kode}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        # Ambil data terbaru
        latest = data.get("data", [{}])[0] if data.get("data") else {}
        return {
            "foreign_buy":  latest.get("foreignBuy", 0),
            "foreign_sell": latest.get("foreignSell", 0),
            "foreign_net":  latest.get("foreignNet", 0),
        }
    except Exception:
        return {"foreign_buy": 0, "foreign_sell": 0, "foreign_net": 0}

def analyze_bandarmology(kode: str, teknikal: dict) -> dict:
    """Gabungkan foreign flow dengan analisa volume dari data teknikal."""
    foreign = get_foreign_flow(kode)
    vol_ratio = teknikal.get("volume_ratio", 1.0)
    harga_naik = teknikal.get("macd", {}).get("histogram", 0) > 0

    score = 0
    if foreign["foreign_net"] > 0:          score += 2
    if vol_ratio > 1.5:                      score += 1
    if harga_naik and vol_ratio > 1.2:       score += 1

    return {
        "kode": kode,
        "foreign_net": foreign["foreign_net"],
        "volume_ratio": vol_ratio,
        "score_bandarmology": score,
        "max_score": 4
    }

if __name__ == "__main__":
    print(json.dumps(analyze_bandarmology("BBCA", {"volume_ratio": 1.8, "macd": {"histogram": 0.5}}), indent=2))
PYEOF
echo -e "${GREEN}  ✓ 03-bandarmology${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 04 — FUNDAMENTAL FILTER
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[5/9] 04-fundamental-filter...${NC}"
mkdir -p "$BASE/04-fundamental-filter/scripts"
cat > "$BASE/04-fundamental-filter/SKILL.md" << 'SKILL'
# Skill: Fundamental Filter
# Aktif saat: Membuat atau mengedit script filter fundamental saham

## PERAN FUNDAMENTAL DI SISTEM INI

Fundamental BUKAN penentu sinyal harian — fungsinya sebagai FILTER AWAL.
Saham dengan fundamental buruk langsung dibuang dari watchlist harian.
Update: cukup mingguan atau saat laporan keuangan keluar (quarterly).

## KRITERIA FILTER (saham LULUS jika memenuhi minimal 3 dari 5)

| Metrik | Nilai Ideal | Keterangan |
|---|---|---|
| PER | < 20 | Tidak terlalu mahal |
| PBV | < 3 | Wajar secara aset |
| ROE | > 10% | Profitabel |
| DER | < 1.5 | Tidak terlalu berhutang |
| Market Cap | > 1T | Cukup likuid |

## SCORING FUNDAMENTAL (maks 5 poin, tiap kriteria terpenuhi = +1)

## CATATAN
Saham growth/teknologi seperti GOTO bisa punya PER tinggi — pertimbangkan
konteks sektornya sebelum mendiskualifikasi.
SKILL

cat > "$BASE/04-fundamental-filter/scripts/fundamental_filter.py" << 'PYEOF'
"""
fundamental_filter.py — Filter fundamental dari SQLite
"""
import sqlite3
import json

DB_PATH = "data/saham.db"

def filter_fundamental(kode: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT per, pbv, roe, market_cap FROM fundamental WHERE kode=?",
        (kode,)).fetchone()
    conn.close()

    if not row:
        return {"kode": kode, "score_fundamental": 0, "lulus": False, "catatan": "Data tidak ada"}

    per, pbv, roe, market_cap = row
    score = 0
    if per and per < 20:              score += 1
    if pbv and pbv < 3:               score += 1
    if roe and roe > 0.10:            score += 1
    if market_cap and market_cap > 1e12: score += 1

    return {
        "kode": kode,
        "per": per, "pbv": pbv, "roe": roe, "market_cap": market_cap,
        "score_fundamental": score,
        "max_score": 4,
        "lulus": score >= 2
    }

if __name__ == "__main__":
    from fetch_data import load_watchlist
    results = [filter_fundamental(k) for k in load_watchlist()]
    print(json.dumps(results, indent=2, default=str))
PYEOF
echo -e "${GREEN}  ✓ 04-fundamental-filter${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 05 — SENTIMENT SCRAPER
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[6/9] 05-sentiment-scraper...${NC}"
mkdir -p "$BASE/05-sentiment-scraper/scripts"
cat > "$BASE/05-sentiment-scraper/SKILL.md" << 'SKILL'
# Skill: Sentiment Scraper
# Aktif saat: Membuat atau mengedit script pengambilan berita & sentimen

## SUMBER BERITA (semua gratis)

| Sumber | Tipe | Library |
|---|---|---|
| Kontan.co.id | RSS feed | feedparser |
| Bisnis.com | RSS feed | feedparser |
| Google News | Search per emiten | feedparser (GNews RSS) |
| IDX Keterbukaan Informasi | Press release resmi | requests + IDX API |

## CARA KERJA
1. Fetch berita 24 jam terakhir per saham di watchlist
2. Filter headline yang mengandung kode/nama saham
3. Kirim kumpulan headline ke LLM untuk scoring sentimen
4. Output: POSITIF / NEGATIF / NETRAL + ringkasan singkat

## SCORING SENTIMENT (maks 3 poin)
```python
if sentiment == "POSITIF":   score = 3
elif sentiment == "NETRAL":  score = 1
elif sentiment == "NEGATIF": score = 0
# Jika ada berita IDX resmi positif (keterbukaan informasi) → bonus +1
```

## SUMBER GOOGLE NEWS RSS
```python
# URL format untuk Google News RSS per saham:
url = f"https://news.google.com/rss/search?q={kode}+saham+IDX&hl=id&gl=ID&ceid=ID:id"
```
SKILL

cat > "$BASE/05-sentiment-scraper/scripts/sentiment_scraper.py" << 'PYEOF'
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
PYEOF
echo -e "${GREEN}  ✓ 05-sentiment-scraper${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 06 — SCORING ENGINE
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[7/9] 06-scoring-engine...${NC}"
mkdir -p "$BASE/06-scoring-engine/scripts"
cat > "$BASE/06-scoring-engine/SKILL.md" << 'SKILL'
# Skill: Scoring Engine
# Aktif saat: Membuat atau mengedit sistem ranking & seleksi saham final

## BOBOT SCORING (total maks ~20 poin)

| Layer | Bobot | Maks Poin |
|---|---|---|
| Teknikal | 30% | 6 poin |
| Bandarmologi | 35% | 4 poin (+1 bonus) |
| Fundamental | 15% | 4 poin |
| Sentimen | 20% | 3 poin (+1 bonus) |

## RUMUS SKOR AKHIR
```python
skor_akhir = (
    (score_teknikal / 6) * 30 +
    (score_bandarmologi / 4) * 35 +
    (score_fundamental / 4) * 15 +
    (score_sentimen / 3) * 20
)
# Skala 0–100. Ambil 3–5 saham dengan skor tertinggi.
```

## FILTER WAJIB SEBELUM MASUK RANKING
- Fundamental lulus (score >= 2) → wajib
- RR Ratio >= 1.5 dari kalkulasi ATR → wajib
- Volume ratio > 0.8 (saham tidak sepi) → wajib

## LABEL SINYAL FINAL
```
Skor >= 70  → ✅ STRONG BUY
Skor 50–69  → 🟡 BUY (selektif)
Skor < 50   → ❌ SKIP (tidak dikirim ke Telegram)
```
SKILL

cat > "$BASE/06-scoring-engine/scripts/scoring_engine.py" << 'PYEOF'
"""
scoring_engine.py — Gabungkan semua layer jadi skor final
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def hitung_skor(teknikal: dict, bandarmologi: dict, fundamental: dict, sentimen_score: int) -> dict:
    kode = teknikal["kode"]

    # Filter wajib
    if not fundamental.get("lulus", False):
        return {"kode": kode, "skor": 0, "sinyal": "❌ SKIP", "alasan": "Fundamental tidak lulus"}
    if teknikal.get("rr", 0) < 1.5:
        return {"kode": kode, "skor": 0, "sinyal": "❌ SKIP", "alasan": "Risk/Reward tidak memadai"}

    s_teknikal     = teknikal.get("score_teknikal", 0)
    s_bandar       = bandarmologi.get("score_bandarmologi", 0)
    s_fundamental  = fundamental.get("score_fundamental", 0)
    s_sentimen     = sentimen_score

    skor = (
        (s_teknikal / 6) * 30 +
        (s_bandar / 4) * 35 +
        (s_fundamental / 4) * 15 +
        (s_sentimen / 3) * 20
    )
    skor = round(skor, 1)

    if skor >= 70:   sinyal = "✅ STRONG BUY"
    elif skor >= 50: sinyal = "🟡 BUY"
    else:            sinyal = "❌ SKIP"

    return {
        "kode": kode,
        "skor": skor,
        "sinyal": sinyal,
        "harga": teknikal.get("harga"),
        "sl": teknikal.get("sl"),
        "tp1": teknikal.get("tp1"),
        "tp2": teknikal.get("tp2"),
        "rr": teknikal.get("rr"),
        "detail": {
            "teknikal": s_teknikal,
            "bandarmologi": s_bandar,
            "fundamental": s_fundamental,
            "sentimen": s_sentimen,
        }
    }

def ranking(results: list, top_n: int = 5) -> list:
    filtered = [r for r in results if r["sinyal"] != "❌ SKIP"]
    sorted_r = sorted(filtered, key=lambda x: x["skor"], reverse=True)
    return sorted_r[:top_n]

if __name__ == "__main__":
    # Contoh test
    dummy = hitung_skor(
        teknikal={"kode":"BBCA","harga":9850,"score_teknikal":5,"rr":2.1,"sl":9550,"tp1":10150,"tp2":10450},
        bandarmologi={"score_bandarmologi":3},
        fundamental={"score_fundamental":4,"lulus":True},
        sentimen_score=2
    )
    print(json.dumps(dummy, indent=2))
PYEOF
echo -e "${GREEN}  ✓ 06-scoring-engine${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 07 — LLM PROMPT
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[8/9] 07-llm-prompt...${NC}"
mkdir -p "$BASE/07-llm-prompt/scripts"
cat > "$BASE/07-llm-prompt/SKILL.md" << 'SKILL'
# Skill: LLM Prompt Engineer
# Aktif saat: Membuat atau mengedit prompt ke OpenRouter / AI provider

## MODEL YANG DIGUNAKAN

| Model | Peran | Endpoint OpenRouter |
|---|---|---|
| deepseek/deepseek-chat:free | Primary analyst | openrouter.ai/api/v1 |
| meta-llama/llama-3.3-70b-instruct:free | Fallback (jika DeepSeek rate limit) | openrouter.ai/api/v1 |
| qwen/qwen3-32b:free | Fallback kedua | openrouter.ai/api/v1 |

## TOKEN MANAGEMENT
- Limit gratis: 50 request/hari, reset 07.00 WIB
- Kirim maksimal 10 headline berita ke LLM (bukan semua)
- Gunakan 1 LLM call per BATCH saham (bukan per saham)
- n8n wajib handle fallback ke model berikutnya jika error 429

## SYSTEM PROMPT
```
Kamu adalah analis saham profesional Indonesia yang berpengalaman di pasar IDX.
Tugasmu menginterpretasi data teknikal, bandarmologi, fundamental, dan sentimen berita
menjadi narasi analisa yang singkat, jelas, dan actionable dalam Bahasa Indonesia.
Selalu gunakan format yang sudah ditentukan. Jangan tambahkan disclaimer panjang.
Fokus pada fakta data dan interpretasi yang tepat.
```

## USER PROMPT TEMPLATE
```
Berikut data analisa untuk saham-saham berikut. Hasilkan narasi singkat per saham:

{data_json}

Format output per saham:
KODE — SINYAL
Harga: Rp X | SL: Rp X | TP1: Rp X | TP2: Rp X | R/R: X
Teknikal: [interpretasi RSI, MACD, tren dalam 1-2 kalimat]
Bandar: [interpretasi foreign flow dan volume dalam 1 kalimat]
Sentimen: [POSITIF/NEGATIF/NETRAL — ringkasan berita dalam 1 kalimat]
Kesimpulan: [1-2 kalimat actionable — kapan dan bagaimana entry]
```
SKILL

cat > "$BASE/07-llm-prompt/scripts/llm_analyst.py" << 'PYEOF'
"""
llm_analyst.py — Kirim data ke OpenRouter, terima narasi analisa
"""
import requests
import json
import os
import time

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "deepseek/deepseek-chat:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-32b:free",
]

SYSTEM_PROMPT = """Kamu adalah analis saham profesional Indonesia yang berpengalaman di pasar IDX.
Tugasmu menginterpretasi data teknikal, bandarmologi, fundamental, dan sentimen berita
menjadi narasi analisa yang singkat, jelas, dan actionable dalam Bahasa Indonesia.
Fokus pada fakta data. Jangan tambahkan disclaimer panjang."""

def build_prompt(saham_list: list) -> str:
    data_str = json.dumps(saham_list, ensure_ascii=False, indent=2)
    return f"""Berikut data analisa saham IDX hari ini. Hasilkan narasi singkat per saham:

{data_str}

Format output per saham (wajib persis seperti ini):
━━━━━━━━━━━━━━━━━━
📊 [KODE] — [SINYAL]
Harga: Rp [X] | SL: Rp [X] | TP1: Rp [X] | TP2: Rp [X] | R/R: [X]x
📈 Teknikal: [interpretasi RSI, MACD, tren — 1-2 kalimat]
🏦 Bandar: [foreign flow dan volume — 1 kalimat]
📰 Sentimen: [POSITIF/NEGATIF/NETRAL — ringkasan berita 1 kalimat]
💡 Kesimpulan: [kapan dan bagaimana entry — 1-2 kalimat actionable]"""

def call_llm(prompt: str, model_index: int = 0) -> str:
    if model_index >= len(MODELS):
        return "Error: Semua model rate limit. Coba lagi nanti."

    model = MODELS[model_index]
    try:
        r = requests.post(OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://saham-ai.local",
                "X-Title": "saham-ai"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            },
            timeout=60
        )

        if r.status_code == 429:
            print(f"  Rate limit {model}, fallback ke model berikutnya...")
            time.sleep(2)
            return call_llm(prompt, model_index + 1)

        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"  Error {model}: {e}")
        return call_llm(prompt, model_index + 1)

def generate_analisa(saham_list: list) -> str:
    prompt = build_prompt(saham_list)
    return call_llm(prompt)

if __name__ == "__main__":
    dummy = [{"kode": "BBCA", "sinyal": "✅ STRONG BUY", "skor": 75,
              "harga": 9850, "sl": 9550, "tp1": 10150, "tp2": 10450, "rr": 2.1,
              "rsi": 52, "macd_hist": 0.5, "foreign_net": 15000000,
              "sentimen": "POSITIF", "berita": ["BBCA cetak laba bersih Q3 naik 12%"]}]
    print(generate_analisa(dummy))
PYEOF
echo -e "${GREEN}  ✓ 07-llm-prompt${NC}"

# ════════════════════════════════════════════════════════════
# SKILL 08 — N8N WORKFLOW
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[9/9] 08-n8n-workflow...${NC}"
mkdir -p "$BASE/08-n8n-workflow/references"
cat > "$BASE/08-n8n-workflow/SKILL.md" << 'SKILL'
# Skill: n8n Workflow Architect
# Aktif saat: Merancang atau mengedit workflow n8n untuk bot saham

## ARSITEKTUR WORKFLOW

### Workflow 1 — Auto Pagi (Schedule)
```
Schedule Trigger (03.30 WIB, Senin-Jumat)
  → Execute Command: python scripts/run_all.py
  → IF: output ada sinyal valid
    → HTTP Request: POST ke /webhook/analisa-saham (workflow 2)
  → IF: error
    → Telegram: kirim notif error ke admin
```

### Workflow 2 — Analisa & Kirim Telegram
```
Webhook Trigger (POST /webhook/analisa-saham)
  → Code Node: parse JSON saham list
  → HTTP Request: POST OpenRouter (primary model)
  → IF: status 429 (rate limit)
    → Wait 3s → HTTP Request: POST OpenRouter (fallback model)
  → Code Node: format pesan Telegram
  → Telegram Node: kirim ke channel/chat ID kamu
```

### Workflow 3 — Manual Trigger via Telegram
```
Telegram Trigger (bot menerima pesan)
  → IF: pesan = "analisa [KODE]"
    → Execute Command: python scripts/run_single.py [KODE]
    → HTTP Request: OpenRouter
    → Telegram: kirim hasil analisa
  → IF: pesan = "watchlist"
    → Execute Command: cat config/watchlist.txt
    → Telegram: kirim daftar watchlist
  → IF: pesan = "status"
    → Execute Command: python scripts/status.py
    → Telegram: kirim status sistem
```

## ENVIRONMENT VARIABLES DI N8N
```
OPENROUTER_API_KEY  → API key OpenRouter
TELEGRAM_BOT_TOKEN  → Token bot Telegram dari @BotFather
TELEGRAM_CHAT_ID    → Chat ID kamu (bisa pakai @userinfobot)
VPS_SCRIPT_PATH     → Path absolut ke folder scripts: /home/user/saham-ai
```

## ERROR HANDLING WAJIB
- Retry maksimal 2x jika Execute Command gagal
- Fallback model jika OpenRouter 429
- Kirim notif error ke Telegram admin jika semua retry gagal
- Jangan retry infinite loop — bisa habiskan quota harian
SKILL

cat > "$BASE/08-n8n-workflow/references/run_all.py" << 'PYEOF'
"""
run_all.py — Script utama yang dipanggil oleh n8n setiap pagi
Output: JSON ke stdout → dibaca oleh n8n
"""
import sys
import os
import json

# Tambahkan path scripts ke sys.path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from fetch_data import load_watchlist, fetch_and_store, init_db
from technical_analysis import analyze
from bandarmology import analyze_bandarmology
from fundamental_filter import filter_fundamental
from sentiment_scraper import collect_sentiment_data
from scoring_engine import hitung_skor, ranking

def run():
    init_db()
    watchlist = load_watchlist()
    print(f"Memproses {len(watchlist)} saham...", file=sys.stderr)

    results = []
    for kode in watchlist:
        try:
            # Fetch data terbaru
            fetch_and_store(kode)

            # Analisa per layer
            teknikal     = analyze(kode)
            fundamental  = filter_fundamental(kode)
            bandar       = analyze_bandarmology(kode, teknikal)
            sentiment_d  = collect_sentiment_data(kode)

            # Sentimen score sementara netral (akan di-score oleh LLM)
            sentimen_score = 1

            # Scoring final
            skor = hitung_skor(teknikal, bandar, fundamental, sentimen_score)
            skor["headlines"] = sentiment_d.get("headlines", [])
            results.append(skor)

            print(f"  ✓ {kode}: {skor['sinyal']} ({skor['skor']})", file=sys.stderr)
        except Exception as e:
            print(f"  ✗ {kode}: {e}", file=sys.stderr)

    # Ambil top 5
    top = ranking(results, top_n=5)
    print(json.dumps(top, ensure_ascii=False))

if __name__ == "__main__":
    run()
PYEOF
echo -e "${GREEN}  ✓ 08-n8n-workflow${NC}"

# ════════════════════════════════════════════════════════════
# SELESAI
# ════════════════════════════════════════════════════════════
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ✅  SEMUA SKILLS BERHASIL DIBUAT                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📁 Struktur:${NC}"
find .agent/skills -type f | sort | sed 's/^/   /'
echo ""
echo -e "${GREEN}Setup VPS selanjutnya:${NC}"
echo "  1. mkdir -p ~/saham-ai/{data,config,scripts,logs}"
echo "  2. pip install yfinance pandas pandas-ta requests feedparser python-telegram-bot"
echo "  3. Salin semua .py dari .agent/skills/*/scripts/ ke ~/saham-ai/scripts/"
echo "  4. Set env: export OPENROUTER_API_KEY=your_key"
echo "  5. Test: python ~/saham-ai/scripts/run_all.py"
echo "  6. Import workflow n8n dan set environment variables"
echo ""
