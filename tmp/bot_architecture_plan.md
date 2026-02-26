# Arsitektur & Perencanaan Fitur Saham AI Bot 2026

Dokumen ini berisi rancangan final fitur, menu, dan format output untuk bot Telegram Saham AI, mempertimbangkan analisa *All-Market* (Bluechip hingga Saham Gorengan) dan teknik *Deep Learning* tingkat lanjut dengan budget Rp 0.

## 1. Daftar Menu & Perintah Bot Telegram

Bot akan memiliki menu interaktif (berupa tombol/keyboard di bawah chat) dan perintah teks (slash commands) agar mudah digunakan.

### A. Menu Utama (Slash Commands)
- `/start` - Menampilkan ucapan selamat datang dan daftar menu utama.
- `/radar` - **[UTAMA]** Menampilkan 5-10 saham rekomendasi terbaik hari ini (hasil filter 3 tier).
- `/cek [KODE_SAHAM]` - Menganalisa 1 saham spesifik secara *real-time/on-demand* (contoh: `/cek BBCA` atau `/cek PANI`).
- `/market_brief` - Menampilkan ringkasan kondisi IHSG hari ini (Global index, Rupiah, Sektoral yang sedang manggung).
- `/watchlist` - Melihat daftar saham pantauan aktif.
- `/add [KODE_SAHAM]` - Menambahkan saham ke watchlist.
- `/del [KODE_SAHAM]` - Menghapus saham dari watchlist.
- `/set_tier` - Mengatur preferensi risiko (Pilih mau dikasih rekomendasi: Hanya Bluechip, Mid-Cap, atau Campur dengan Gorengan).

### B. Menu Keyboard Interaktif (Tombol di bawah chat)
1. 🎯 **Sinyal Hari Ini** (Sama dengan `/radar`)
2. 🔍 **Cek Saham** (Akan meminta input kode saham)
3. 📉 **Kondisi Market** (Sama dengan `/market_brief`)
4. ⚙️ **Pengaturan** (Watchlist & Tier Risiko)

---

## 2. Struktur Pengelompokan Saham (Multi-Tier Screening)

Untuk memberikan 5-10 pilihan saham, bot akan memecah rekomendasinya berdasarkan profil risiko/tier, agar *trader* bisa memilih sesuai selera hari itu:

- **TIER 1 (Bluechip / Big Cap):** Saham aman, likuiditas raksasa, pergerakan lambat tapi pasti. (Cocok untuk dana besar, *Swing* santai).
- **TIER 2 (Mid-Cap / Trending):** Saham lapis dua yang sedang ada momentum sektoral atau narasi kuat. (Cocok untuk *Swing* agresif 1-2 minggu).
- **TIER 3 (Small-Cap / Gorengan):** Saham dengan volatilitas ekstrem, ada ledakan volume tiba-tiba. (Cocok untuk *Day Trading / Fast Trade*, Wajib pantau layar).

---

## 3. Contoh Output Bot Telegram

Berikut adalah wujud nyata pesan yang akan dikirimkan bot saat Anda menekan `/radar` atau otomatis setiap pagi. Bot akan menyajikan **5-10 saham**, dibagi per Tier agar rapi.

### 🌅 Output `/radar` (Morning Briefing / Sinyal Harian)

```text
🚀 RADAR SAHAM AI 2026 🚀
📅 Rabu, 27 Februari 2026 | 06:00 WIB
💡 Rekomendasi 7 Saham Terbaik (Skor > 70)

🏢 TIER 1: BLUECHIP (Aman & Stabil)
━━━━━━━━━━━━━━━━━━
1️⃣ BBCA (.JK) — ✅ STRONG BUY (Skor: 88)
🔖 Harga: Rp 9.850
🎯 Entry: Rp 9.800 – 9.850
🛑 SL: Rp 9.550 (Risiko KETAT -3.1% via ATR)
🏁 TP1: Rp 10.150 | TP2: Rp 10.450
🧠 Analisa Pro: MACD Golden Cross di oversold. VWAP naik stabil membuktikan uang besar mulai masuk diam-diam. Sentimen laporan keuangan rekor (IndoBERT).

2️⃣ AMMN (.JK) — 🟡 BUY ON WEAKNESS (Skor: 75)
🔖 Harga: Rp 8.200 | SL: Rp 7.950 | TP: Rp 8.800
🧠 Analisa Pro: Sedang koreksi sehat di atas EMA 34. Tunggu pantulan di area 8.150.

🔥 TIER 2: MID-CAP TRENDING (Momentum Kuat)
━━━━━━━━━━━━━━━━━━
3️⃣ PANI (.JK) — ✅ STRONG BUY (Skor: 85)
🔖 Harga: Rp 5.400
🎯 Entry: Atas Rp 5.450 (Breakout)
🛑 SL: Rp 5.050
🏁 TP1: Rp 6.000 (R/R: 1.5x)
🧠 Analisa Pro: Sinyal TMT (Tulip Momentum Trend) menyala! Harga bertahan solid di atas EMA 13. Sektor properti sedang rotasi masuk.

4️⃣ BRPT (.JK) — ✅ BUY (Skor: 80)
🔖 Harga: Rp 1.120 | SL: Rp 1.050 | TP: Rp 1.250
🧠 Analisa Pro: Bollinger Band Squeeze mulai membuka ke atas. Volume 2x lipat dari rata-rata.

⚡ TIER 3: GORENGAN / HIGH VOLATILITY (Fast Trade Only!)
━━━━━━━━━━━━━━━━━━
5️⃣ CUAN (.JK) — 🚨 HIGH RISK BUY (Skor: 82)
🔖 Harga: Rp 6.800
🎯 Entry: HAKA jika open langsung loncat, atau antre di 6.700.
🛑 SL: Rp 6.400 (WAJIB DISIPLIN!)
🏁 TP1: Bebas (Trailing Stop jika jebol EMA 5 menit)
🧠 Analisa Pro: Ledakan volume (Spike) > 350% kemarin sore menjelang closing. Ada jejak Smart Money / Cornering. Jangan ditinggal tidur!

6️⃣ BREN (.JK) — 🚨 HIGH RISK BUY (Skor: 78)
🔖 Harga: Rp 7.200 | SL: Rp 6.900
🧠 Analisa Pro: Mantul agresif dari support kuat, stochastic RSI (3,3,14) memberi sinyal reversal instan.

--------------------
🤖 Prediksi Deep Learning (LSTM): Market IHSG hari ini probabilitas 65% ditutup HIJAU. Sektor Energi & Properti diprediksi memimpin.
⚠️ Disclaimer: Not financial advice. Pastikan sesuaikan lot sizing dengan toleransi risiko Anda.
```

### 🔍 Output `/cek UNVR` (Analisis On-Demand)

```text
📊 ANALISA INSTAN: UNVR (.JK)
📅 Waktu: 27 Feb 2026, 10:15 WIB

⚠️ STATUS: SKIP / WAIT & SEE (Skor: 45/100)

🔖 Harga Saat Ini: Rp 2.850

📈 Teknikal (Bearish):
- Harga masih tertahan di bawah garis EMA 13, 34, dan 89 (Downtrend Kuat).
- Terjadi Hidden Bearish Divergence (Harga pantul sedikit, tapi RSI melemah).

🏦 Bandarmologi / Volume (Distribusi):
- OBV (On-Balance Volume) terus menukik tajam.
- VWAP berada di Rp 2.900 (Harga saat ini di bawah VWAP rata-rata bandar harian).

📰 Sentimen (IndoBERT):
- 🟥 NEGATIF (-0.8). Dominasi berita penurunan daya beli dan kompetisi produk.

💡 Kesimpulan Trader Pro:
Jangan tangkap pisau jatuh! Meski terlihat murah (Fundamental PER turun), secara *price action* belum ada tanda-tanda *Smart Money* masuk membalikkan arah. Tunggu sampai minimal harga break di atas Rp 3.000 dengan volume spike.
```
