import os
import subprocess
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

def get_python_executable():
    """Mengambil path python dari virtual environment jika ada, jika tidak fallback ke sys.executable"""
    venv_python = os.path.join(BASE_DIR, 'venv', 'bin', 'python3')
    if not os.path.exists(venv_python):
        venv_python = os.path.join(BASE_DIR, 'venv', 'bin', 'python')
    if not os.path.exists(venv_python):
        # Fallback Windows
        venv_python = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
        
    return venv_python if os.path.exists(venv_python) else sys.executable

def run_script(script_name, args=None):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    print(f"\n{'='*60}")
    print(f"🚀 MENJALANKAN: {script_name}")
    print(f"{'='*60}")
    
    python_exe = get_python_executable()
    cmd = [python_exe, script_path]
    if args:
        cmd.extend(args)
        
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n[!] TERJADI KESALAHAN KRITIKAL: Eksekusi {script_name} gagal (Kode: {result.returncode}).")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Saham AI - Master Engine Runner')
    parser.add_argument('--ticker', type=str, help='Ticker saham spesifik untuk dianalisa (opsional)')
    args = parser.parse_args()

    ticker_args = ['--ticker', args.ticker] if args.ticker else []

    print("\n" + "#"*60)
    print("🌟 SAHAM AI: MASTER ENGINE RUNNER 🌟".center(60))
    if args.ticker:
        print(f"🎯 ANALISA SPESIFIK: {args.ticker.upper()}".center(60))
    print("#"*60 + "\n")
    
    # Urutan eksekusi
    run_script('01_data_collector.py', ticker_args)
    run_script('02_technical_analyst.py', ticker_args)
    run_script('03_bandarmology.py', ticker_args)
    run_script('04_fundamental_filter.py', ticker_args)
    run_script('05_sentiment_scraper.py', ticker_args)
    run_script('06_scoring_engine.py', ticker_args)
    run_script('07_llm_formatter.py', ticker_args)
        
    print("\n" + "#"*60)
    print("✅ SELURUH PROSES ANALISA BERHASIL DIJALANKAN!".center(60))
    print("📄 File llm_payload.json sudah di-generate untuk N8N.".center(60))
    print("🤖 Menunggu webhook N8N menembakkan data ini ke Telegram.".center(60))
    print("#"*60 + "\n")
