#!/usr/bin/env python3
"""
BusLiner Database Viewer
========================
Inspects and pretty-prints registered carriers, drivers, and users from db/busliner.db.
Usage:
    python3 server/view_db.py
"""

import os
import sys
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "busliner.db")

def print_table(title: str, headers: list, rows: list):
    print("\n" + "=" * 80)
    print(f"📊 {title} (Всего: {len(rows)})")
    print("=" * 80)
    if not rows:
        print("  [Пусто] Нет записей в базе данных.\n")
        return

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(val or "—")))

    # Header
    header_str = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    print(header_str)
    print("-" * len(header_str))

    # Rows
    for row in rows:
        row_str = " | ".join(f"{str(val or '—'):<{col_widths[i]}}" for i, val in enumerate(row))
        print(row_str)
    print()

def main():
    if not os.path.exists(DB_PATH):
        print(f"\n⚠️  Файл базы данных пока не создан: {DB_PATH}")
        print("Запустите сервис telegram_auth_bot.py, чтобы база инициализировалась.\n")
        return

    print(f"\n📁 База данных: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. CARRIERS
        cursor.execute("SELECT id, company_name, unp, iban, vehicle_plate, route, created_at FROM carriers ORDER BY id DESC")
        carriers = cursor.fetchall()
        print_table("ПЕРЕВОЗЧИКИ (ИП / ЮРЛИЦА)", ["ID", "Компания / ИП", "УНП", "IBAN", "Борт", "Основной маршрут", "Дата регистрации"], carriers)

        # 2. DRIVERS
        cursor.execute("SELECT id, full_name, username, phone, carrier_name, status, created_at FROM drivers ORDER BY id DESC")
        drivers = cursor.fetchall()
        print_table("ВОДИТЕЛИ АВТОПАРКА", ["ID", "ФИО / Имя", "Telegram", "Телефон", "Прикреплен к перевозчику", "Статус", "Дата регистрации"], drivers)

        # 3. USERS
        cursor.execute("SELECT id, telegram_id, username, full_name, role, created_at FROM users ORDER BY id DESC")
        users = cursor.fetchall()
        print_table("АВТОРИЗОВАННЫЕ ПОЛЬЗОВАТЕЛИ (TELEGRAM / WEB)", ["ID", "Telegram ID", "Username", "Имя", "Роль", "Дата входа"], users)

        conn.close()
    except Exception as e:
        print(f"❌ Ошибка чтения базы данных: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
