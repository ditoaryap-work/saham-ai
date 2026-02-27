import os
import subprocess
import json
from fastapi import FastAPI, HTTPException
from typing import Optional

app = FastAPI(title="Saham AI API", description="Microservice pengambil dan penganalisa data saham")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
PAYLOAD_PATH = os.path.join(BASE_DIR, 'data', 'llm_payload.json')

def get_python_executable():
    """Mengambil path python dari virtual environment jika ada"""
    venv_python = os.path.join(BASE_DIR, 'venv', 'bin', 'python3')
    if not os.path.exists(venv_python):
        venv_python = os.path.join(BASE_DIR, 'venv', 'bin', 'python')
    if not os.path.exists(venv_python):
        # Fallback Windows
        venv_python = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
    return venv_python if os.path.exists(venv_python) else "python3"

def run_script(script_name, ticker=None):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    python_exe = get_python_executable()
    
    cmd = [python_exe, script_path]
    if ticker:
        cmd.extend(['--ticker', ticker])
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Gagal mengeksekusi {script_name}. Error: {result.stderr}")
    return True

@app.get("/cek")
async def cek_saham(ticker: str):
    """
    Menjalankan seluruh alur analisa untuk 1 ticker spesifik dan
    mengembalikan field JSON yang siap dikirim langsung ke OpenRouter.
    """
    try:
        ticker = ticker.upper()
        
        # 1. Jalankan Engine secara berurutan
        run_script('01_data_collector.py', ticker)
        run_script('02_technical_analyst.py', ticker)
        run_script('03_bandarmology.py', ticker)
        run_script('04_fundamental_filter.py', ticker)
        run_script('05_sentiment_scraper.py', ticker)
        run_script('06_scoring_engine.py', ticker)
        run_script('07_llm_formatter.py', ticker)
        
        # 2. Baca Hasil payload JSON dan langsung jadikan HTTP Response
        if not os.path.exists(PAYLOAD_PATH):
             raise HTTPException(status_code=404, detail="File payload gagal di-generate oleh engine.")
             
        with open(PAYLOAD_PATH, 'r') as f:
            data = json.load(f)
            
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/radar")
async def radar_harian():
    """
    Menjalankan seluruh alur analisa (semua ticker dalam watchlist).
    Digunakan untuk cron job harian.
    """
    try:
        run_script('01_data_collector.py')
        run_script('02_technical_analyst.py')
        run_script('03_bandarmology.py')
        run_script('04_fundamental_filter.py')
        run_script('05_sentiment_scraper.py')
        run_script('06_scoring_engine.py')
        run_script('07_llm_formatter.py')
        
        if not os.path.exists(PAYLOAD_PATH):
             raise HTTPException(status_code=404, detail="File payload gagal di-generate oleh engine.")
             
        with open(PAYLOAD_PATH, 'r') as f:
            data = json.load(f)
            
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def ping():
    return {"status": "ok", "message": "Saham AI Local Engine Running!"}

if __name__ == "__main__":
    import uvicorn
    # Menjalankan server di port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
