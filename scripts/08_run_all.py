import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

# Urutan eksekusi sangat penting
scripts_to_run = [
    '01_data_collector.py',
    '02_technical_analyst.py',
    '03_bandarmology.py',
    '04_fundamental_filter.py',
    '05_sentiment_scraper.py',
    '06_scoring_engine.py',
    '07_llm_formatter.py'
]

def run_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    print(f"\n{'='*60}")
    print(f"🚀 MENJALANKAN: {script_name}")
    print(f"{'='*60}")
    
    # Eksekusi menggunakan python environment yang sedang aktif
    result = subprocess.run([sys.executable, script_path])
    
    if result.returncode != 0:
        print(f"\n[!] TERJADI KESALAHAN KRITIKAL: Eksekusi {script_name} gagal (Kode: {result.returncode}).")
        print("[!] Proses dibatalkan untuk menghindari kerusakan data.")
        sys.exit(1)

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("🌟 SAHAM AI: MASTER ENGINE RUNNER 🌟".center(60))
    print("#"*60 + "\n")
    
    for script in scripts_to_run:
        run_script(script)
        
    print("\n" + "#"*60)
    print("✅ SELURUH PROSES ANALISA BERHASIL DIJALANKAN!".center(60))
    print("📄 File llm_payload.json sudah di-generate untuk N8N.".center(60))
    print("🤖 Menunggu webhook N8N menembakkan data ini ke Telegram.".center(60))
    print("#"*60 + "\n")
