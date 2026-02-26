# PROJECT MEMORY — saham-ai
# Transfer dokumen ini ke Antigravity workspace saham-ai
# Baca ini sebelum memulai sesi apapun

---

## APA INI
Bot sinyal saham IDX otomatis berbasis Python + n8n + Telegram.
Mengirim 3–5 sinyal saham terbaik setiap pagi jam 04.00 WIB
dan bisa di-trigger manual via chat Telegram.

---

## INFRASTRUKTUR YANG SUDAH DIMILIKI
- VPS (aktif, siap deploy Python + n8n)
- n8n (sudah terinstall di VPS)
- Telegram Bot (perlu dibuat via @BotFather)
- OpenRouter free (50 req/hari, reset 07.00 WIB)

---

## TECH STACK
| Komponen | Teknologi |
|---|---|
| Data harga | yfinance (.JK suffix untuk IDX) |
| Indikator teknikal | pandas-ta |
| Storage | SQLite (data/saham.db) |
| Orkestrasi | n8n (3 workflow) |
| AI Narasi | OpenRouter — DeepSeek V3 (primary), Llama 3.3 70B (fallback), Qwen3 32B (fallback 2) |
| Notifikasi | Telegram Bot API |

---

## SISTEM ANALISA — 4 LAYER

### Layer 1: Teknikal (bobot 30%)
RSI(14), MACD(12,26,9), SMA(20,50,200), BB(20,2), Stochastic, ATR(14), Volume Ratio
Scoring maks: 6 poin

### Layer 2: Bandarmologi (bobot 35%) — paling penting di IDX
Foreign flow (net buy/sell asing dari IDX API), Volume spike (>1.5x avg 5 hari), Price-volume confirmation
Scoring maks: 4 poin (+1 bonus)

### Layer 3: Fundamental (bobot 15%) — hanya sebagai filter awal
PER < 20, PBV < 3, ROE > 10%, Market Cap > 1T
Update: mingguan / per laporan keuangan
Scoring maks: 4 poin

### Layer 4: Sentimen Berita (bobot 20%)
Sumber: Google News RSS, Kontan RSS, Bisnis RSS, IDX keterbukaan informasi
Scrape 24 jam terakhir, kirim headline ke LLM untuk scoring
Scoring maks: 3 poin (+1 bonus berita resmi IDX)

---

## RUMUS SKOR AKHIR
```
skor = (teknikal/6)*30 + (bandar/4)*35 + (fundamental/4)*15 + (sentimen/3)*20
Skala 0–100
>= 70  → ✅ STRONG BUY (dikirim ke Telegram)
50–69  → 🟡 BUY (dikirim jika slot masih ada)
< 50   → ❌ SKIP
```

---

## FORMAT OUTPUT TELEGRAM
```
━━━━━━━━━━━━━━━━━━
📊 BBCA — ✅ STRONG BUY
Harga: Rp 9.850 | SL: Rp 9.550 | TP1: Rp 10.150 | TP2: Rp 10.450 | R/R: 2.1x
📈 Teknikal: RSI netral 52, MACD baru bullish crossover, harga di atas SMA20 & SMA50
🏦 Bandar: Foreign net buy Rp 15M, volume 1.8x rata-rata — ada akumulasi
📰 Sentimen: POSITIF — laba bersih Q3 naik 12% YoY
💡 Kesimpulan: Entry di area 9.800–9.900, tunggu konfirmasi open market
```

---

## STRUKTUR FILE DI VPS
```
~/saham-ai/
├── scripts/
│   ├── fetch_data.py          ← ambil data yfinance + fundamental
│   ├── technical_analysis.py  ← hitung semua indikator
│   ├── bandarmology.py        ← foreign flow + volume spike
│   ├── fundamental_filter.py  ← filter saham layak analisa
│   ├── sentiment_scraper.py   ← scrape berita RSS + Google News
│   ├── scoring_engine.py      ← gabungkan 4 layer jadi skor final
│   ├── llm_analyst.py         ← kirim ke OpenRouter, terima narasi
│   └── run_all.py             ← script utama dipanggil n8n
├── config/
│   └── watchlist.txt          ← daftar kode saham (1 per baris)
├── data/
│   └── saham.db               ← SQLite storage
└── logs/
    └── run.log
```

---

## N8N — 3 WORKFLOW
1. **Auto Pagi**: Schedule 03.30 WIB → run_all.py → OpenRouter → Telegram
2. **Analisa & Kirim**: Webhook → parse JSON → LLM → format → Telegram
3. **Manual Telegram**: Perintah chat → trigger analisa saham spesifik

---

## OPENROUTER — STRATEGI HEMAT TOKEN
- 50 request/hari gratis, reset 07.00 WIB
- Kirim semua saham dalam 1 LLM call (bukan per saham)
- Maksimal 10 headline berita per request
- n8n auto-fallback jika model kena rate limit 429
- Jika serius: top up $10 → limit naik jadi 1000 req/hari

---

## WATCHLIST DEFAULT
BBCA, BBRI, TLKM, ASII, GOTO, BREN, MDKA, ADMR, BMRI, UNVR
(bisa diubah di config/watchlist.txt kapan saja)

---

## STRATEGI TRADING YANG DIDUKUNG
- Swing trading (2–5 hari)
- Daily trading
- Entry: open market, sebelum istirahat, sebelum closing
- SL/TP dihitung otomatis dari ATR(14) per saham
- Bot juga beri sinyal tunggu jika kondisi support/resistance belum ideal

---

## SKILLS YANG TERSEDIA (9 skills)
00-validation-flow     → validasi sebelum eksekusi
01-data-collector      → fetch yfinance + IDX + RSS
02-technical-analyst   → kalkulasi indikator + scoring
03-bandarmology        → foreign flow + volume spike
04-fundamental-filter  → filter fundamental awal
05-sentiment-scraper   → scrape berita + Google News
06-scoring-engine      → gabungkan 4 layer, ranking, filter
07-llm-prompt          → template prompt OpenRouter + fallback
08-n8n-workflow        → arsitektur 3 workflow n8n + Telegram

---

## CATATAN PENTING
- Data bandarmologi detail (broker summary) ada di Stockbit Pro (Rp 200rb/bln)
  → sangat direkomendasikan jika ingin akurasi bandar lebih tinggi
- Semua analisa adalah ACUAN, bukan jaminan profit
- Manajemen risiko tetap di tangan trader (kamu)
- Bot ini untuk keperluan personal, bukan komersial
