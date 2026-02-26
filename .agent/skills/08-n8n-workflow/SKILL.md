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
