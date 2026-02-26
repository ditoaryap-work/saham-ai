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
