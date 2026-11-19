import os
import sys
import time
import subprocess
import re
import signal
import threading

BASE_DIR = r"C:\chromaNexus"
os.chdir(BASE_DIR)

print("=" * 60, flush=True)
print("ChronaNexus — Production Server & Cloudflare Tunnel", flush=True)
print("=" * 60, flush=True)

processes = []

def cleanup(signum=None, frame=None):
    print("\nStopping all services...", flush=True)
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
    print("All services stopped.", flush=True)
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# 1. Start Backend on port 8000
print("[1/3] Starting FastAPI backend on port 8000...", flush=True)
env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"
env["ENVIRONMENT"] = "development"
env["LLM_PROVIDER"] = "ollama"
env["EMBEDDING_PROVIDER"] = "ollama"
env["PYTHONPATH"] = BASE_DIR

backend_p = subprocess.Popen(
    [sys.executable, "-u", "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=BASE_DIR,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)
processes.append(backend_p)

def monitor_backend():
    for line in iter(backend_p.stdout.readline, ''):
        if not line:
            break
        cleaned = line.strip()
        if cleaned:
            print(f"      [Backend]: {cleaned}", flush=True)

threading.Thread(target=monitor_backend, daemon=True).start()

# Wait for backend health
import urllib.request
backend_ready = False
for i in range(60):
    time.sleep(1)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/health", timeout=1) as res:
            if res.status == 200:
                print("      Backend is online and healthy!", flush=True)
                backend_ready = True
                break
    except Exception:
        pass

if not backend_ready:
    print("      Proceeding (backend still initializing in background)...", flush=True)

# 2. Start Unified Gateway on port 3000
print("[2/3] Starting Unified Production Gateway on port 3000...", flush=True)
gateway_p = subprocess.Popen(
    [sys.executable, "-u", "gateway.py"],
    cwd=BASE_DIR,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
processes.append(gateway_p)
time.sleep(1)
print("      Unified Gateway active on http://127.0.0.1:3000", flush=True)

# 3. Start Cloudflare Tunnel with HTTP/2 protocol
print("[3/3] Establishing Cloudflare Tunnel (HTTP/2) for port 3000...", flush=True)
cloudflared_exe = os.path.join(BASE_DIR, "cloudflared.exe")
tunnel_p = subprocess.Popen(
    [cloudflared_exe, "tunnel", "--protocol", "http2", "--url", "http://127.0.0.1:3000"],
    cwd=BASE_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)
processes.append(tunnel_p)

tunnel_url = None

def drain_tunnel():
    global tunnel_url
    for line in iter(tunnel_p.stdout.readline, ''):
        if not line:
            break
        m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if m and not tunnel_url:
            tunnel_url = m.group(0)
            print("\n" + "=" * 60, flush=True)
            print(">>> CHRONANEXUS LIVE TUNNEL READY FOR YOUR FRIEND! <<<", flush=True)
            print(f"Public URL: {tunnel_url}", flush=True)
            print("=" * 60 + "\n", flush=True)
            with open("TUNNEL_PUBLIC_URL.txt", "w", encoding="utf-8") as f:
                f.write(tunnel_url)

threading.Thread(target=drain_tunnel, daemon=True).start()

# Wait for tunnel URL
for _ in range(30):
    if tunnel_url:
        break
    time.sleep(1)

print("Desktop is running as an active server for your friend.", flush=True)
print("Keep this process running. To stop, press Ctrl+C.", flush=True)

try:
    while True:
        time.sleep(1)
        for p in processes:
            if p.poll() is not None:
                print(f"Warning: A service exited with code {p.returncode}", flush=True)
except KeyboardInterrupt:
    cleanup()
