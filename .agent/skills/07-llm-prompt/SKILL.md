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
