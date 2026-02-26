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
