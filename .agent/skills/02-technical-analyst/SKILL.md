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
