#!/usr/bin/env python3
"""
BusLiner Academic Demo Launcher
=============================================================================
One-click unified server and presentation runner for university demo.
Serves:
  - Quiet Luxury B2C deck & search: http://localhost:8080/index.html
  - Passenger Cabinet & AI Sniper:   http://localhost:8080/passenger-cabinet.html
  - Carrier Office & Driver Cockpit: http://localhost:8080/carrier-workspace.html
  - 3D Three.js Minibus Demo:        http://localhost:8080/seat-picker-3d-demo.html
  - REST API Engine:                 http://localhost:8080/api/trips
"""

import sys
import os
import time
import socket
import webbrowser
import threading

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from server.telegram_auth_bot import run_auth_server

DEFAULT_PORT = 8080

def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) != 0

def open_browser_delayed(url: str, delay: float = 1.2):
    time.sleep(delay)
    try:
        webbrowser.open_new_tab(url)
    except Exception:
        pass

def main():
    os.chdir(PROJECT_DIR)

    # 1. Resolve host and port from environment or defaults
    host = os.getenv("HOST") or os.getenv("BUSLINER_AUTH_HOST", "0.0.0.0")
    env_port = os.getenv("PORT") or os.getenv("BUSLINER_AUTH_PORT")

    if env_port:
        try:
            port = int(env_port)
        except ValueError:
            port = DEFAULT_PORT
    else:
        port = DEFAULT_PORT
        if not is_port_available(port, host="127.0.0.1"):
            for p in range(8081, 8095):
                if is_port_available(p, host="127.0.0.1"):
                    port = p
                    break

    # 2. Detect headless execution mode (Docker, cloud container, CI/CD, or CLI flag)
    is_headless = (
        os.getenv("HEADLESS", "").lower() in ("1", "true", "yes") or
        os.getenv("NO_BROWSER", "").lower() in ("1", "true", "yes") or
        "--headless" in sys.argv or
        "--no-browser" in sys.argv
    )

    display_host = "localhost" if host == "0.0.0.0" else host
    demo_url = f"http://{display_host}:{port}/index.html"

    print("=" * 72)
    print("      BUSLINER // ЭКОСИСТЕМА МЕЖДУГОРОДНЕЙ МОБИЛЬНОСТИ")
    print("      (Демонстрационный сервер для защиты проекта и облачного деплоя)")
    print("=" * 72)
    print(f"  [+] Многопоточный HTTP & REST API сервер запущен на {host}:{port}")
    print(f"  [+] Главная страница:      {demo_url}")
    print(f"  [+] Кабинет пассажира:     http://{display_host}:{port}/passenger-cabinet.html")
    print(f"  [+] Кабинет перевозчика:   http://{display_host}:{port}/carrier-workspace.html")
    print(f"  [+] REST API рейсов:       http://{display_host}:{port}/api/trips")
    print(f"  [+] Healthcheck:           http://{display_host}:{port}/health")
    if is_headless:
        print("  [+] Режим без браузера активен (HEADLESS=1 / Cloud Container)")
    else:
        print("  [+] Открываем браузер автоматически...")
    print("=" * 72)
    print("  Для остановки сервера нажмите Ctrl + C")
    print("=" * 72)

    # Launch browser only if interactive desktop mode
    if not is_headless:
        t = threading.Thread(target=open_browser_delayed, args=(demo_url,), daemon=True)
        t.start()

    # Start main server (blocking loop)
    run_auth_server(host=host, port=port)

if __name__ == "__main__":
    main()
