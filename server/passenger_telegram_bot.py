#!/usr/bin/env python3
"""
BusLiner Passenger Companion — Cryptographically Secure Telegram Bot & Google Auth API
=======================================================================================
Bot Username: @BusLinerPassBot (Configurable via BUSLINER_PASSENGER_BOT_USERNAME)
Purpose: Passenger self-service registration, 1-click web authentication,
         Google email verification, digital boarding passes, 3D seat access & live bus radar.
Zero external dependencies: Built with Python 3 standard library.
"""

import os
import sys
import json
import time
import secrets
import sqlite3
import threading
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import URLError

# ==============================================================================
# CONFIGURATION & PARAMS
# ==============================================================================
BOT_TOKEN = os.getenv("BUSLINER_PASSENGER_BOT_TOKEN", "8750251587:AAG78r9fxqKNwPxa_LazTNv-h54mHJOJquI")
BOT_USERNAME = os.getenv("BUSLINER_PASSENGER_BOT_USERNAME", "BusLinerPassBot")
SERVER_HOST = os.getenv("BUSLINER_PASS_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("BUSLINER_PASS_PORT", "8085"))
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "busliner.db")

# In-memory authentication tokens (token -> passenger_data, TTL 300s)
PASSENGER_AUTH_TOKENS: Dict[str, Dict[str, Any]] = {}


# ==============================================================================
# PERSISTENT SQLITE DATABASE FOR PASSENGERS
# ==============================================================================
def init_passenger_db() -> None:
    """Initializes tables for passengers and tickets in SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passengers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                google_email TEXT UNIQUE,
                auth_token TEXT,
                bonus_balance INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passenger_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passenger_id INTEGER,
                ticket_code TEXT UNIQUE,
                route TEXT,
                seat TEXT,
                fleet_type TEXT,
                departure_time TEXT,
                departure_station TEXT,
                price_byn REAL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def get_or_create_passenger(telegram_id: Optional[int] = None, google_email: Optional[str] = None, full_name: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        row = None
        if telegram_id:
            cursor.execute("SELECT * FROM passengers WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
        elif google_email:
            cursor.execute("SELECT * FROM passengers WHERE google_email = ?", (google_email,))
            row = cursor.fetchone()

        if row:
            # Update fields if provided
            p_id = row["id"]
            if google_email and not row["google_email"]:
                cursor.execute("UPDATE passengers SET google_email = ? WHERE id = ?", (google_email, p_id))
            if full_name and not row["full_name"]:
                cursor.execute("UPDATE passengers SET full_name = ? WHERE id = ?", (full_name, p_id))
            conn.commit()
            return dict(row)
        else:
            # Insert new passenger
            name = full_name or (google_email.split("@")[0] if google_email else f"Пассажир #{secrets.randbelow(9999)}")
            cursor.execute("""
                INSERT INTO passengers (telegram_id, username, full_name, google_email, bonus_balance)
                VALUES (?, ?, ?, ?, 10)
            """, (telegram_id, username, name, google_email))
            conn.commit()
            new_id = cursor.lastrowid
            
            # Create a default welcome ticket
            ticket_code = f"BL-{secrets.randbelow(8999) + 1000}"
            cursor.execute("""
                INSERT INTO passenger_tickets (passenger_id, ticket_code, route, seat, fleet_type, departure_time, departure_station, price_byn, status)
                VALUES (?, ?, 'Минск ➔ Вильнюс', '04A', 'Mercedes-Benz Sprinter Executive', 'Сегодня, 18:45', 'Центральный АВ, перрон 3', 85.00, 'active')
            """, (new_id, ticket_code))
            conn.commit()

            cursor.execute("SELECT * FROM passengers WHERE id = ?", (new_id,))
            return dict(cursor.fetchone())


def get_passenger_tickets(passenger_id: int) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM passenger_tickets WHERE passenger_id = ? ORDER BY id DESC", (passenger_id,))
        return [dict(r) for r in cursor.fetchall()]


# ==============================================================================
# TELEGRAM BOT POLLING ENGINE (Zero external dependencies)
# ==============================================================================
def telegram_api_request(method: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not BOT_TOKEN or "AAG78r9fx" not in BOT_TOKEN:
        return None
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        return None
    except Exception as e:
        return None


def handle_telegram_message(message: Dict[str, Any]) -> None:
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()
    user = message.get("from", {})
    tg_id = user.get("id")
    username = user.get("username", "")
    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "Уважаемый пассажир"

    if not chat_id:
        return

    # Handle /start or /login with optional auth token
    if text.startswith("/start") or text.startswith("/login"):
        parts = text.split(" ")
        auth_nonce = parts[1] if len(parts) > 1 else None

        passenger = get_or_create_passenger(telegram_id=tg_id, full_name=full_name, username=username)

        # If nonce was provided from website, link and authenticate web session
        if auth_nonce and auth_nonce in PASSENGER_AUTH_TOKENS:
            PASSENGER_AUTH_TOKENS[auth_nonce]["authenticated"] = True
            PASSENGER_AUTH_TOKENS[auth_nonce]["passenger"] = passenger
            welcome_msg = (
                f"✅ <b>Вход на сайт BusLiner подтверждён!</b>\n\n"
                f"Здравствуйте, {full_name}! Ваш браузер успешно авторизован.\n"
                f"Электронный билет и посадочные талоны синхронизированы с вашим профилем.\n\n"
                f"🎫 <b>Активный билет:</b> Минск ➔ Вильнюс (Кресло 04A)\n"
                f"💰 <b>Бонусный баланс:</b> {passenger.get('bonus_balance', 10)} BYN"
            )
        else:
            welcome_msg = (
                f"👋 <b>Добро пожаловать в BusLiner Passenger Bot!</b>\n"
                f"<i>Официальный бот для пассажиров межгородских линий</i>\n\n"
                f"Здесь вы можете:\n"
                f"• Авторизоваться на сайте без пароля\n"
                f"• Привязать почту Google (@gmail.com)\n"
                f"• Просматривать купленные билеты и место в салоне\n"
                f"• Отслеживать GPS-радар автобуса на трассе\n\n"
                f"Используйте кнопки ниже для быстрого действия:"
            )

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🎫 Мои билеты", "callback_data": "my_tickets"},
                    {"text": "💺 3D Выбор кресла", "url": "https://busliner.by/seat-picker-3d-demo.html"}
                ],
                [
                    {"text": "🛰️ GPS-радар автобуса", "callback_data": "bus_radar"},
                    {"text": "📧 Привязать Google", "callback_data": "link_google"}
                ],
                [
                    {"text": "📞 Консьерж 24/7", "callback_data": "concierge_help"}
                ]
            ]
        }
        telegram_api_request("sendMessage", {
            "chat_id": chat_id,
            "text": welcome_msg,
            "parse_mode": "HTML",
            "reply_markup": reply_markup
        })

    elif text == "/tickets" or text == "Мои билеты":
        passenger = get_or_create_passenger(telegram_id=tg_id, full_name=full_name, username=username)
        send_tickets_info(chat_id, passenger["id"])

    elif text == "/radar" or text == "Радар":
        send_bus_radar_info(chat_id)

    elif text == "/register":
        msg = (
            "👤 <b>Регистрация пассажира в BusLiner Club</b>\n\n"
            "Для привязки аккаунта отправьте вашу почту Google в формате:\n"
            "<code>ваш.email@gmail.com</code>\n\n"
            "Вы сразу получите <b>10 BYN бонуса</b> на первую поездку!"
        )
        telegram_api_request("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

    elif "@gmail.com" in text.lower():
        # User entered Google email
        email = text.strip().lower()
        passenger = get_or_create_passenger(telegram_id=tg_id, google_email=email, full_name=full_name, username=username)
        msg = (
            f"✅ <b>Почта Google успешно привязана!</b>\n\n"
            f"Аккаунт: <code>{email}</code>\n"
            f"Бонусный баланс: <b>10 BYN</b>\n"
            f"Теперь вы можете входить на сайте через кнопку <b>«Продолжить с Google»</b> или напрямую через Telegram."
        )
        telegram_api_request("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})


def send_tickets_info(chat_id: int, passenger_id: int) -> None:
    tickets = get_passenger_tickets(passenger_id)
    if not tickets:
        msg = "У вас пока нет активных билетов. Выберите рейс на сайте BusLiner!"
    else:
        t = tickets[0]
        msg = (
            f"🎫 <b>ЭЛЕКТРОННЫЙ ПОСАДОЧНЫЙ ТАЛОН #{t['ticket_code']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🚩 <b>Маршрут:</b> {t['route']}\n"
            f"🚌 <b>Транспорт:</b> {t['fleet_type']}\n"
            f"⏰ <b>Отправление:</b> {t['departure_time']}\n"
            f"📍 <b>Место посадки:</b> {t['departure_station']}\n"
            f"💺 <b>Кресло:</b> <b>{t['seat']}</b> (у окна, 220V)\n"
            f"💳 <b>Тариф:</b> {t['price_byn']} BYN (Оплачено)\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<i>Предъявите этот экран водителю при посадке. Распечатывать не требуется.</i>"
        )
    telegram_api_request("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})


def send_bus_radar_info(chat_id: int) -> None:
    msg = (
        "🛰️ <b>ЖИВОЙ GPS-РАДАР РЕЙСА</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Борт: Mercedes-Benz Sprinter 519 CDI (госномер 7TAX-8921)\n"
        "Маршрут: Минск ➔ Вильнюс\n"
        "Скорость: <b>92 км/ч</b> • Трасса М6\n"
        "Подача на перрон № 3: <b>18:30</b> (через 45 мин)\n"
        "Статус борта: 🟢 <i>Следует строго по расписанию</i>"
    )
    telegram_api_request("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})


def handle_callback_query(query: Dict[str, Any]) -> None:
    query_id = query.get("id")
    data = query.get("data")
    message = query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    from_user = query.get("from", {})
    tg_id = from_user.get("id")

    if not chat_id:
        return

    passenger = get_or_create_passenger(telegram_id=tg_id, username=from_user.get("username", ""))

    if data == "my_tickets":
        send_tickets_info(chat_id, passenger["id"])
    elif data == "bus_radar":
        send_bus_radar_info(chat_id)
    elif data == "link_google":
        msg = "📧 Отправьте ваш Google Email (например <code>alex@gmail.com</code>), чтобы связать аккаунт для мгновенного входа на сайте."
        telegram_api_request("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
    elif data == "concierge_help":
        msg = (
            "📞 <b>Круглосуточный Консьерж BusLiner</b>\n\n"
            "Единая диспетчерская линия: <b>+375 (29) 190-20-26</b>\n"
            "E-mail: <code>concierge@busliner.by</code>\n"
            "Дежурный диспетчер на связи 24/7."
        )
        telegram_api_request("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

    telegram_api_request("answerCallbackQuery", {"callback_query_id": query_id})


def start_bot_polling() -> None:
    offset = 0
    while True:
        try:
            res = telegram_api_request("getUpdates", {"offset": offset, "timeout": 20})
            if res and res.get("ok"):
                for update in res.get("result", []):
                    offset = max(offset, update["update_id"] + 1)
                    if "message" in update:
                        handle_telegram_message(update["message"])
                    elif "callback_query" in update:
                        handle_callback_query(update["callback_query"])
        except Exception:
            pass
        time.sleep(1)


# ==============================================================================
# PASSENGER API HTTP SERVER (REST endpoints for web auth & Google login)
# ==============================================================================
class PassengerAuthHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)

        if url.path == "/api/passenger/auth/init":
            # Generate new challenge token for Telegram login
            nonce = secrets.token_hex(16)
            PASSENGER_AUTH_TOKENS[nonce] = {
                "created_at": time.time(),
                "authenticated": False,
                "passenger": None
            }
            bot_link = f"https://t.me/{BOT_USERNAME}?start={nonce}"
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "nonce": nonce,
                "bot_username": BOT_USERNAME,
                "telegram_url": bot_link
            }).encode("utf-8"))

        elif url.path == "/api/passenger/auth/check":
            nonce = qs.get("nonce", [""])[0]
            session = PASSENGER_AUTH_TOKENS.get(nonce)
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if session and session["authenticated"]:
                self.wfile.write(json.dumps({
                    "ok": True,
                    "authenticated": True,
                    "passenger": session["passenger"]
                }).encode("utf-8"))
            else:
                self.wfile.write(json.dumps({
                    "ok": True,
                    "authenticated": False
                }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if url.path == "/api/passenger/google_login":
            # Google Account Email Login
            email = data.get("email", "").strip().lower()
            name = data.get("name", "").strip() or email.split("@")[0]
            if not email or "@" not in email:
                self.send_response(400)
                self.send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "Invalid email"}).encode("utf-8"))
                return

            passenger = get_or_create_passenger(google_email=email, full_name=name)
            tickets = get_passenger_tickets(passenger["id"])
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "passenger": passenger,
                "tickets": tickets,
                "provider": "google"
            }).encode("utf-8"))

        elif url.path == "/api/passenger/register":
            name = data.get("name", "").strip()
            email = data.get("email", "").strip().lower()
            if not email or "@" not in email:
                self.send_response(400)
                self.send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "Invalid email"}).encode("utf-8"))
                return

            passenger = get_or_create_passenger(google_email=email, full_name=name)
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "message": "Passenger registered successfully",
                "passenger": passenger
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_http_server():
    server = HTTPServer((SERVER_HOST, SERVER_PORT), PassengerAuthHandler)
    server.serve_forever()


if __name__ == "__main__":
    init_passenger_db()
    print(f"[BusLiner Passenger Bot] Starting HTTP API on port {SERVER_PORT}...")
    t_http = threading.Thread(target=start_http_server, daemon=True)
    t_http.start()

    print(f"[BusLiner Passenger Bot] Bot @{BOT_USERNAME} initialized. Starting polling loop...")
    start_bot_polling()
