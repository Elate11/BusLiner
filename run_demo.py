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
    port = DEFAULT_PORT
    if not is_port_available(port):
        for p in range(8081, 8095):
            if is_port_available(p):
                port = p
                break

    demo_url = f"http://localhost:{port}/index.html"

    print("=" * 72)
    print("      BUSLINER // ЭКОСИСТЕМА МЕЖДУГОРОДНЕЙ МОБИЛЬНОСТИ")
    print("      (Демонстрационный сервер для защиты проекта в вузе)")
    print("=" * 72)
    print(f"  [+] Многопоточный HTTP & REST API сервер запущен на порту: {port}")
    print(f"  [+] Главная страница:      {demo_url}")
    print(f"  [+] Кабинет пассажира:     http://localhost:{port}/passenger-cabinet.html")
    print(f"  [+] Кабинет перевозчика:   http://localhost:{port}/carrier-workspace.html")
    print(f"  [+] REST API рейсов:       http://localhost:{port}/api/trips")
    print("=" * 72)
    print("  Открываем браузер автоматически...")
    print("  Для остановки сервера нажмите Ctrl + C")
    print("=" * 72)

    # Launch browser in separate background thread
    t = threading.Thread(target=open_browser_delayed, args=(demo_url,), daemon=True)
    t.start()

    # Start main server (blocking loop)
    run_auth_server(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
