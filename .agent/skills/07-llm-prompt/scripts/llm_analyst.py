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
