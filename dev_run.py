# dev_run.py
import os
import sys
import time
import signal
import subprocess
from watchfiles import watch, PythonFilter

APP_CMD = [sys.executable, 'app.py']
IGNORE = {'.venv', 'third_party', '__pycache__', '.git'}

def start_app():
    print("▶️  starting app...")
    # CREATE_NEW_PROCESS_GROUP lets us send CTRL_BREAK_EVENT on Windows if needed
    creationflags = 0
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen(
        APP_CMD,
        creationflags=creationflags,
        close_fds=False
    )

def stop_app(proc):
    if proc and proc.poll() is None:
        print("⏹  stopping previous app...")
        try:
            if os.name == 'nt':
                # try graceful terminate
                proc.terminate()
            else:
                proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print("🛠  force kill...")
            if os.name == 'nt':
                proc.kill()
            else:
                proc.send_signal(signal.SIGKILL)
            proc.wait()

def main():
    proc = start_app()
    print("🔁 watching for changes (Ctrl+C to quit)\n")

    try:
        for _changes in watch('.', watch_filter=PythonFilter(ignore_paths=IGNORE)):
            os.system('cls' if os.name == 'nt' else 'clear')
            print("✏️  changes detected, restarting...\n")
            stop_app(proc)
            proc = start_app()
    except KeyboardInterrupt:
        print("\n👋 bye!")
    finally:
        stop_app(proc)

if __name__ == '__main__':
    main()
