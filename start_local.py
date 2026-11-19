import os
import sys
import time
import subprocess
import signal
import urllib.request

BASE_DIR = r"C:\chromaNexus"
os.chdir(BASE_DIR)

print("=" * 60, flush=True)
print("ChronaNexus — Local Development Server (No Tunneling)", flush=True)
print("=" * 60, flush=True)

processes = []

def cleanup(signum=None, frame=None):
    print("\nStopping local servers...", flush=True)
    for p in reversed(processes):
        try:
            p.terminate()
        except Exception:
            pass
    time.sleep(1)
    for p in reversed(processes):
        try:
            p.kill()
        except Exception:
            pass
    print("All local servers stopped.", flush=True)
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# 1. Start FastAPI Backend on port 8000
print("[1/2] Starting FastAPI backend on http://127.0.0.1:8000 ...", flush=True)
env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"
env["ENVIRONMENT"] = "development"
env["PYTHONPATH"] = BASE_DIR

backend_p = subprocess.Popen(
    [sys.executable, "-u", "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=BASE_DIR,
    env=env
)
processes.append(backend_p)

# Wait for backend health
backend_ready = False
for i in range(30):
    time.sleep(1)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/health", timeout=1) as res:
            if res.status == 200:
                print("      Backend is online and healthy!", flush=True)
                backend_ready = True
                break
    except Exception:
        pass

# 2. Start Vite Frontend on http://localhost:5173
print("[2/2] Starting Vite Frontend on http://localhost:5173 ...", flush=True)
frontend_p = subprocess.Popen(
    ["cmd.exe", "/c", "npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
    cwd=BASE_DIR
)
processes.append(frontend_p)

print("\n" + "=" * 60, flush=True)
print(">>> ChronaNexus is running locally (No Tunneling) <<<", flush=True)
print("Frontend App: http://localhost:5173", flush=True)
print("API Backend:  http://127.0.0.1:8000", flush=True)
print("API Docs:     http://127.0.0.1:8000/docs", flush=True)
print("=" * 60 + "\n", flush=True)

try:
    while True:
        time.sleep(1)
        for p in processes:
            if p.poll() is not None:
                print(f"Warning: A local service exited with code {p.returncode}", flush=True)
except KeyboardInterrupt:
    cleanup()

