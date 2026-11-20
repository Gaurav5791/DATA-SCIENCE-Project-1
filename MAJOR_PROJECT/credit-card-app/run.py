import os
import sys
import time
import threading
import webbrowser
import uvicorn

def open_browser():
    """Wait briefly for Uvicorn to bind the socket, then pop open the dashboard."""
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n[INFO] Automatically opening browser at {url} ...\n")
    webbrowser.open(url)

def main():
    # Ensure current working directory is credit-card-app
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    print("=" * 70)
    print("  CREDIT CARD TRANSACTION ANALYTICS DASHBOARD")
    print("  Server URL : http://127.0.0.1:8000")
    print("  Opening browser automatically...")
    print("  Press CTRL+C in this terminal to stop the server.")
    print("=" * 70)

    # Launch browser in a background daemon thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI server
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
