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
