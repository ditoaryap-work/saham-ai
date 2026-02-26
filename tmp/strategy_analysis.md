# Analisa Strategi Trading Saham AI 2026

Dokumen ini berisi analisa mendalam mengenai usulan 6 strategi trading (berdasarkan referensi internet) yang akan ditanamkan ke dalam bot Telegram Saham AI, beserta evaluasi teknis, kelebihan, kekurangan, dan fitur tambahan wajib yang dibutuhkan Sistem AI untuk mengeksekusinya tanpa API berbayar.

## Evaluasi 6 Strategi Usulan

### 1. Day Trade (Perdagangan Harian Reguler)
- **Konsep:** Beli pagi/siang, jual hari itu juga sebelum jam penutupan jam 16:00 WIB. Pantang menahan posisi menginap (*Overnight*).
- **Syarat Mutlak Bot:** Likuiditas super tinggi, volatilitas *Intraday* harian konstan. Indikator wajib: VWAP, EMA 3 menit/5 menit, dan MACD *Intraday*.
- **Evaluasi AI:** *Mungkin dilakukan dengan delay 15 menit dari yfinance.* Fitur wajib: **Real-time Alert Engine**. Jika AI deteksi harga tembus garis VWAP ke atas dengan volume melonjak di jam 10 pagi, bot harus langsung *nge-ping* Telegram Anda saat itu juga.

### 2. Swing Pendek (1-5 Hari Bursa)
- **Konsep:** Memanfaatkan momentum rotasi sektoral yang berlangsung hitungan hari. Beli saat mau *breakout* atau di harga *support* EMA ketat, jual saat nyentuh resisten terdekat.
- **Syarat Mutlak Bot:** Kombinasi *Moving Average Crossover* (contoh EMA 13 motong EMA 34 ke atas), Bollinger Band menyempit (Squeeze), skor Bandarmologi Positif dari rentang 5 hari terakhir.
- **Evaluasi AI:** Sangat ideal & akurasi tinggi untuk bot kita. Algoritma 4 Layer kita (Teknikal, Bandar, Fundamental, Sentimen) di `MEMORY-saham-ai.md` paling unggul di sini. Fitur wajib: **Auto Trailing Stop Calculator** (Kirim pesan kapan Anda harus naikin SL buat ngunci profit).

### 3. Swing Low (Buy on Weakness Ekstrem / Rebound Hunter)
- **Konsep:** Menangkap "pisau jatuh". Beli saham bagus (Bluechip turun harga) yang sedang *downtrend* sesaat karena *panic selling* atau *news* sentimen negatif sesaat, namun fundamentalnya kuat.
- **Syarat Mutlak Bot:** RSI Oversold ekstrem (< 20), *Hidden Bullish Divergence* (MACD/RSI merangkak naik padahal harga masih turun), pantulan dari EMA 200 Weekly.
- **Evaluasi AI:** Strategi terbaik menguji nyali bandar. *AI IndoBERT sangat vital di sini.* Jika AI baca sentimen berita turun karena gosip/hoax, skor Swing Low tinggi. Tapi kalau berita karena Direktur korupsi/PKPU, AI wajib skor 0 (Skip). Fitur wajib: **Fundamental Discount Filter** (Pastikan PER & PBV saham turun signifikan di bawah historikal 5 tahunnya).

### 4. BSJP ARA HUNTER (Beli Sore Jual Pagi - Memburu Saham Auto Reject Atas)
- **Konsep:** Jam 15:45 (Pre-Closing), bot mencari saham "Gorengan" atau Lapis 2 yang dikunci di puncak harganya (ARA). Tujuannya beli nge-HAKA di harga penutupan, berharap besok pagi saat market buka (09:00 WIB) loncat (Gap Up) minimal 2-5% untuk langsung dibuang (Take Profit hitungan detik).
- **Syarat Mutlak Bot:** Pantau lonjakan *Volume Spike* gila-gilaan bertepatan harga mengunci batas ARA (contoh: +34% untuk harga < 200, +25% untuk 200-2000, +20% harga > 2000). Tidak boleh ada antrean jual (Offer kosong).
- **Evaluasi AI:** Cukup berbahaya. Karena delay *yfinance*, bot mungkin terlambat memberitahu Anda 15 menit. Solusi: VPS bot diatur menari data **jam 15:30 WIB tajam**, lalu memuntahkan "Calon ARA Hunter" dalam 1 menit sebelum market masuk *Pre-Closing* 15:55. Fitur wajib: **ARA Lock Detector** (% kenaikan hari ini).

### 5. BSJP DAY (Beli Sore Jual Pagi Konvensional - Pola Candlestick Reversal)
- **Konsep:** Hampir mirip dengan ARA Hunter, tapi mencari saham yang TIDAK ARA. Fokus cari saham yang seharian memerah, tapi mulai jam 14:30 ditarik naik kuat membentuk *Hammer Candlestick* panjang ber-volume di *support* penentu.
- **Syarat Mutlak Bot:** Deteksi pola *Hammer*, *Piercing Line*, atau *Engulfing* di TF (Timeframe) *Daily* menjelang closing.
- **Evaluasi AI:** Ini *Golden Goose* (Tambang emas) trader Harian. Model *Deep Learning LSTM* kita akan berjaya di sini. AI memprediksi, "Saham ini hari ini ditarik naik dari batas bawahnya. Probabilitas besok pagi Open-nya nge-Gap Up adalah 72%."

### 6. BSJP ARB HUNTER (Memburu Saham Auto Reject Bawah)
- **Konsep:** *High Risk, High Return.* Membeli saham gorengan di level ARB (Auto Reject Bawah) berhari-hari, TEPAT pada momen "gembok" antrean belinya dijebol Bandar raksasa (ribuan lot pindah tangan dari Offer ke Bid dalam sedetik). Tujuannya nge-dorong harga agar *mantul* (Technical Rebound).
- **Syarat Mutlak Bot:** Hanya melihat perubahan Bid/Offer (Tape Reading).
- **Evaluasi AI:** ⚠️ **WARNING! Kritis.** *yfinance* TIDAK PUNYA data *real-time Orderbook* (Bid/Offer Lot). Sistem kita butuh mata yang memantau lot detik-per-detik. Strategi ini MUSTAHIL 100% akurat tanpa API berbayar (seperti Stockbit/IPOT). Saran AI: **Ubah strategi menjadi "Post-ARB Rebound"**. Cari saham yang rontok parah, tapi hari ini *Candle-nya Doji (Plus putih kecil)* ber-volume besar, di sana AI Anda masuk layar untuk beraksi tanpa *Orderbook*.

---

## 🔥 Kesimpulan Pembangunan Fitur (Wajib Ditambahkan)

Setelah membedah 6 strategi *Tier-God* ritel di atas, saya selaku Arsitek AI menyimpulkan bahwa bot n8n Anda **WAJIB MEMILIKI 3 MENU TRIGGER WAKTU (SCHEDULER)** baru yang akan saya buat:

1.  **Trigger 1 (08:45 WIB - "Morning Briefing"):** N8n mengirim rangkuman *Swing Pendek* & *Swing Low*. Alert saham apa yang harus dipantau hari itu.
2.  **Trigger 2 (10:00 & 14:00 WIB - "Intraday Radar"):** N8n melempar pesan dadakan (*Push Notif*) untuk peluang **Day Trade**. "BBCA volume melonjak 200%, VWAP tembus! Sinyal Day Trade AKTIF."
3.  **Trigger 3 (15:35 WIB - "Screener BSJP"):** *Waktu Krusial!* Bot mengirim list khusus **BSJP Day** & **ARA Hunter**, agar Anda punya waktu 15 menit untuk HAKA di penutupan market. (Catatan: ARB Hunter kita main aman via pancingan *Candle Doji* di dasar).

Dokumen ini akan menjadi landasan baru saat kita merancang urat nadi `scoring_engine.py` dan Alur N8N selanjutnya.
