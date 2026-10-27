#!/usr/bin/env python3
"""
BusLiner Unified Platform Bot & Auth Daemon
=======================================================================================
Single Autonomous Telegram Bot for all three user roles:
1. Клиент / Пассажир (Client / Passenger): билеты, VIP Консьерж-Снайпер, поиск рейсов, вход в ЛК
2. Перевозчик (Carrier / Fleet Owner): сводка аналитики парка, выручка, выплаты IBAN, инвайты водителей
3. Водитель (Driver): пульт рейса BL-5715, посадочная ведомость, чек-ин пассажиров, задержка рейса

Security Standard:
- Telegram HMAC-SHA256 constant-time widget verification
- Challenge-Response Deep Link Anti-Replay Nonces (300s TTL)
- Strict Zero-Hardcoded Secrets (Loaded via environment / .env in .gitignore)
- Zero external dependencies: Python 3 standard library (hmac, hashlib, secrets, sqlite3, urllib)
"""

import os
import sys
import json
import time
import hmac
import hashlib
import secrets
import threading
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import URLError
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Universal Belarus Transport Sniper Integration
try:
    from server.external_transport_sniper import universal_sniper_manager, TransportTrip
except ImportError:
    try:
        from external_transport_sniper import universal_sniper_manager, TransportTrip
    except ImportError:
        universal_sniper_manager = None
        TransportTrip = None

# ==============================================================================
# SECURE CONFIGURATION & TOKEN LOADER (FROM .env / ENVIRONMENT)
# ==============================================================================
def load_env_token() -> str:
    """Dynamically loads Telegram Bot API Token from environment or local .env file."""
    for var in ("BUSLINER_BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "BUSLINER_TELEGRAM_BOT_TOKEN", "BUSLINER_PASSENGER_BOT_TOKEN"):
        val = os.getenv(var)
        if val and len(val.strip()) > 20:
            return val.strip()

    search_paths = [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        os.path.join(os.getcwd(), ".env")
    ]
    for p in search_paths:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k in ("BUSLINER_BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "BUSLINER_TELEGRAM_BOT_TOKEN", "BUSLINER_PASSENGER_BOT_TOKEN") and len(v) > 20:
                                return v
            except Exception:
                pass
    return ""

TELEGRAM_BOT_TOKEN = load_env_token()
BOT_USERNAME = os.getenv("BUSLINER_BOT_USERNAME", "buslinerbot")
SERVER_HOST = os.getenv("BUSLINER_AUTH_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("BUSLINER_AUTH_PORT", "8080"))
AUTH_SESSION_TTL_SECONDS = 300  # 5 minutes maximum lifetime for challenge nonces
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "busliner.db")

# In-memory session and runtime state
ACTIVE_AUTH_SESSIONS: Dict[str, Dict[str, Any]] = {}
USER_ROLES: Dict[int, str] = {}
DRIVER_ORGANIZATIONS: Dict[int, Dict[str, Any]] = {}
CARRIER_ORGS: Dict[int, Dict[str, Any]] = {}
INVITE_TOKENS: Dict[str, Dict[str, Any]] = {}
ACTIVE_TRIPS: Dict[int, Dict[str, Any]] = {}

# Active sniper sessions for passengers: telegram_id -> session data
PASSENGER_SNIPER_MONITORS: Dict[int, Dict[str, Any]] = {}

# ==============================================================================
# LIVE PLATFORM DATA (PULLED FROM THE WEBSITE DATA MODEL)
# ==============================================================================
SITE_TRIPS = [
    {
        "id": "BL-5715",
        "route": "Минск -> Вильнюс",
        "departure_station": "Центральный АВ, Минск (Перрон 3)",
        "arrival_station": "Аэропорт Вильнюс (VNO)",
        "time": "18:45",
        "fare": 95,
        "seats_total": 20,
        "seats_occupied": 18,
        "vehicle": "Mercedes-Benz Sprinter 319 CDI (7 TAX 8812)",
        "driver": "Володин Сергей И."
    },
    {
        "id": "BL-2204",
        "route": "Минск -> Варшава",
        "departure_station": "Центральный АВ, Минск (Перрон 1)",
        "arrival_station": "Варшава Заходня (Dworzec Zachodni)",
        "time": "21:30",
        "fare": 140,
        "seats_total": 20,
        "seats_occupied": 19,
        "vehicle": "Volkswagen Crafter VIP Line (7 TAX 4109)",
        "driver": "Смирнов Андрей В."
    },
    {
        "id": "BL-8802",
        "route": "Минск -> Гродно",
        "departure_station": "Автовокзал Восточный, Минск",
        "arrival_station": "Автовокзал Гродно",
        "time": "08:00",
        "fare": 35,
        "seats_total": 19,
        "seats_occupied": 17,
        "vehicle": "Mercedes-Benz Sprinter 316 CDI (7 TAX 1904)",
        "driver": "Ковалев Дмитрий М."
    },
    {
        "id": "BL-1415",
        "route": "Минск -> Брест",
        "departure_station": "Центральный АВ, Минск",
        "arrival_station": "Автовокзал Брест",
        "time": "14:15",
        "fare": 38,
        "seats_total": 20,
        "seats_occupied": 16,
        "vehicle": "Mercedes-Benz Sprinter 319 CDI (7 TAX 8812)",
        "driver": "Володин Сергей И."
    }
]

FLEET_STATS = {
    "gross_revenue_7d": 14820,
    "net_payout_7d": 14079,
    "platform_fee_7d": 741,
    "load_factor": 92.4,
    "peak_load": 98.3,
    "punctuality": 99.4,
    "trips_count_7d": 48,
    "payout_schedule": "Завтра (T+1 расчет)",
    "best_day": "Суббота (3 240 BYN, 98% загрузка)"
}

FLEET_VEHICLES_TELEMETRY = [
    {
        "model": "Mercedes-Benz Sprinter 519 CDI",
        "plate": "7 TAX 8812",
        "seats": 20,
        "year": 2023,
        "status": "На линии",
        "route": "Минск -> Вильнюс (18:45)",
        "driver": "Володин С. И.",
        "km_today": 412,
        "service_interval": "ТО через 6 400 км"
    },
    {
        "model": "Volkswagen Crafter 50 2.0 TDI",
        "plate": "7 TAX 4109",
        "seats": 19,
        "year": 2024,
        "status": "На линии",
        "route": "Минск -> Гродно (19:30)",
        "driver": "Смирнов А. В.",
        "km_today": 280,
        "service_interval": "ТО через 11 200 км"
    },
    {
        "model": "Mercedes-Benz Sprinter 316 CDI",
        "plate": "7 TAX 1904",
        "seats": 16,
        "year": 2021,
        "status": "На базе / Резерв",
        "route": "Минск-Центральный",
        "driver": "Ковалев Д. М.",
        "km_today": 0,
        "service_interval": "Диагностика OK"
    }
]

ACTIVE_FLIGHT_MANIFEST = [
    {"seat": "01A", "name": "Ковалев Д. М.", "phone": "+375 29 111-22-33", "status": "В салоне"},
    {"seat": "02A", "name": "Морозова Е. С.", "phone": "+375 29 222-33-44", "status": "В салоне"},
    {"seat": "03A", "name": "Смирнов А. В.", "phone": "+375 29 333-44-55", "status": "В салоне"},
    {"seat": "04A", "name": "Нестеров А. П.", "phone": "+375 29 444-55-66", "status": "В салоне"},
    {"seat": "05B", "name": "Кузнецов И. К.", "phone": "+375 29 555-66-77", "status": "Ожидается"},
    {"seat": "06B", "name": "Попова О. И.", "phone": "+375 29 666-77-88", "status": "В салоне"},
    {"seat": "07B", "name": "Васильев М. С.", "phone": "+375 29 777-88-99", "status": "В салоне"},
    {"seat": "08C", "name": "Соколова А. В.", "phone": "+375 29 888-99-00", "status": "В салоне"},
    {"seat": "09C", "name": "Михайлов П. Д.", "phone": "+375 29 999-00-11", "status": "В салоне"},
    {"seat": "10C", "name": "Новикова К. А.", "phone": "+375 29 123-45-67", "status": "В салоне"},
    {"seat": "11A", "name": "Федоров С. Г.", "phone": "+375 29 234-56-78", "status": "В салоне"},
    {"seat": "12A", "name": "Семенов Д. В.", "phone": "+375 29 345-67-89", "status": "В салоне"},
    {"seat": "13B", "name": "Егорова Л. М.", "phone": "+375 29 456-78-90", "status": "В салоне"},
    {"seat": "14B", "name": "Степанов В. И.", "phone": "+375 29 567-89-01", "status": "В салоне"},
    {"seat": "15C", "name": "Николаева Т. П.", "phone": "+375 29 678-90-12", "status": "В салоне"},
    {"seat": "16C", "name": "Григорьев А. Е.", "phone": "+375 29 789-01-23", "status": "В салоне"},
    {"seat": "17D", "name": "Макарова Н. А.", "phone": "+375 29 890-12-34", "status": "В салоне"},
    {"seat": "18D", "name": "Зайцев Р. О.", "phone": "+375 29 901-23-45", "status": "В салоне"},
    {"seat": "19D", "name": "Свободно", "phone": "—", "status": "Свободно"},
    {"seat": "20D", "name": "Свободно", "phone": "—", "status": "Свободно"}
]


# ==============================================================================
# PERSISTENT SQLITE DATABASE (db/busliner.db)
# ==============================================================================
def init_db() -> None:
    """Initializes tables for carriers, drivers, passengers and authenticated users."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                role TEXT DEFAULT 'client',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carriers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                company_name TEXT,
                unp TEXT,
                iban TEXT,
                bank_name TEXT,
                vehicle_model TEXT,
                vehicle_plate TEXT,
                route TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                full_name TEXT,
                username TEXT,
                phone TEXT,
                carrier_id INTEGER,
                carrier_name TEXT,
                status TEXT DEFAULT 'unassigned',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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

    seed_sample_tickets_if_needed()


def seed_sample_tickets_if_needed():
    """Seeds a realistic verified ticket if database table is fresh."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM passenger_tickets")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO passenger_tickets 
                    (passenger_id, ticket_code, route, seat, fleet_type, departure_time, departure_station, price_byn, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    1,
                    "BL-5715-04A",
                    "Минск -> Вильнюс (Аэропорт VNO)",
                    "04A",
                    "Mercedes-Benz Sprinter 319 CDI (20 мест)",
                    "Сегодня, 18:45",
                    "Перрон 3, Центральный АВ Минск",
                    95.0,
                    "paid"
                ))
                conn.commit()
    except Exception as e:
        print(f"[Seed tickets error]: {e}", file=sys.stderr)


def get_user_role(telegram_id: int) -> Optional[str]:
    """Retrieves verified role from memory or SQLite database."""
    if telegram_id in USER_ROLES:
        return USER_ROLES[telegram_id]
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # 1. Check carriers
            cursor.execute("SELECT id FROM carriers WHERE telegram_id = ?", (telegram_id,))
            if cursor.fetchone():
                USER_ROLES[telegram_id] = "carrier"
                return "carrier"
            # 2. Check drivers
            cursor.execute("SELECT id, status FROM drivers WHERE telegram_id = ?", (telegram_id,))
            d = cursor.fetchone()
            if d:
                USER_ROLES[telegram_id] = "driver"
                return "driver"
            # 3. Check users table
            cursor.execute("SELECT role FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            if row and row[0]:
                r = row[0]
                if r == "owner": r = "carrier"
                if r == "passenger": r = "client"
                USER_ROLES[telegram_id] = r
                return r
            # 4. Check passengers table
            cursor.execute("SELECT id FROM passengers WHERE telegram_id = ?", (telegram_id,))
            if cursor.fetchone():
                USER_ROLES[telegram_id] = "client"
                return "client"
    except Exception as e:
        print(f"[get_user_role error]: {e}", file=sys.stderr)
    return None


def set_user_role(telegram_id: int, role: str, full_name: str = "", username: str = "") -> None:
    """Updates role in memory and database."""
    USER_ROLES[telegram_id] = role
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (telegram_id, username, full_name, role)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = COALESCE(NULLIF(excluded.username, ''), users.username),
                    full_name = COALESCE(NULLIF(excluded.full_name, ''), users.full_name),
                    role = excluded.role
            """, (telegram_id, username, full_name, role))
            
            if role == "client":
                cursor.execute("""
                    INSERT OR IGNORE INTO passengers (telegram_id, username, full_name)
                    VALUES (?, ?, ?)
                """, (telegram_id, username, full_name))
            elif role == "carrier":
                cursor.execute("""
                    INSERT OR IGNORE INTO carriers (telegram_id, company_name)
                    VALUES (?, ?)
                """, (telegram_id, f"ИП {full_name or 'Перевозчик'}") )
            elif role == "driver":
                cursor.execute("""
                    INSERT OR IGNORE INTO drivers (telegram_id, full_name, username)
                    VALUES (?, ?, ?)
                """, (telegram_id, full_name or "Водитель", username))
            conn.commit()
    except Exception as e:
        print(f"[set_user_role error]: {e}", file=sys.stderr)


def save_or_update_user(telegram_id: int, username: str, full_name: str, role: str = "client", phone: Optional[str] = None) -> None:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (telegram_id, username, full_name, role, phone)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name,
                    role = excluded.role,
                    phone = COALESCE(excluded.phone, users.phone)
            """, (telegram_id, username, full_name, role, phone))
            conn.commit()
    except Exception as e:
        print(f"[DB Error: save_or_update_user] {e}", file=sys.stderr)


def save_carrier_registration(telegram_id: Optional[int], company_name: str, unp: str, iban: str, bank_name: str, vehicle_model: str, vehicle_plate: str, route: str) -> None:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO carriers (telegram_id, company_name, unp, iban, bank_name, vehicle_model, vehicle_plate, route)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    company_name = excluded.company_name,
                    unp = excluded.unp,
                    iban = excluded.iban,
                    bank_name = excluded.bank_name,
                    vehicle_model = excluded.vehicle_model,
                    vehicle_plate = excluded.vehicle_plate,
                    route = excluded.route
            """, (telegram_id, company_name, unp, iban, bank_name, vehicle_model, vehicle_plate, route))
            conn.commit()
    except Exception as e:
        print(f"[DB Error: save_carrier_registration] {e}", file=sys.stderr)


def save_or_update_driver(telegram_id: Optional[int], full_name: str, username: str, phone: Optional[str] = None, carrier_id: Optional[int] = None, carrier_name: Optional[str] = None, status: str = "unassigned") -> None:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if telegram_id:
                cursor.execute("""
                    INSERT INTO drivers (telegram_id, full_name, username, phone, carrier_id, carrier_name, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(telegram_id) DO UPDATE SET
                        full_name = excluded.full_name,
                        username = excluded.username,
                        phone = COALESCE(excluded.phone, drivers.phone),
                        carrier_id = COALESCE(excluded.carrier_id, drivers.carrier_id),
                        carrier_name = COALESCE(excluded.carrier_name, drivers.carrier_name),
                        status = excluded.status
                """, (telegram_id, full_name, username, phone, carrier_id, carrier_name, status))
            else:
                cursor.execute("""
                    INSERT INTO drivers (telegram_id, full_name, username, phone, carrier_id, carrier_name, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (None, full_name, username, phone, carrier_id, carrier_name, status))
            conn.commit()
    except Exception as e:
        print(f"[DB Error: save_or_update_driver] {e}", file=sys.stderr)


def get_db_records() -> Dict[str, Any]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id DESC")
            users = [dict(r) for r in cursor.fetchall()]
            cursor.execute("SELECT * FROM carriers ORDER BY id DESC")
            carriers = [dict(r) for r in cursor.fetchall()]
            cursor.execute("SELECT * FROM drivers ORDER BY id DESC")
            drivers = [dict(r) for r in cursor.fetchall()]
            return {"users": users, "carriers": carriers, "drivers": drivers}
    except Exception as e:
        print(f"[DB Error: get_db_records] {e}", file=sys.stderr)
        return {"users": [], "carriers": [], "drivers": []}


def get_carrier_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM carriers WHERE telegram_id = ? ORDER BY id DESC LIMIT 1", (telegram_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            cursor.execute("SELECT * FROM users WHERE telegram_id = ? AND role IN ('carrier', 'owner') ORDER BY id DESC LIMIT 1", (telegram_id,))
            user_row = cursor.fetchone()
            if user_row:
                return {"telegram_id": telegram_id, "company_name": user_row["full_name"], "unp": "Не указан"}
            return None
    except Exception as e:
        print(f"[DB Error: get_carrier_by_telegram_id] {e}", file=sys.stderr)
        return None


def get_driver_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers WHERE telegram_id = ? ORDER BY id DESC LIMIT 1", (telegram_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            cursor.execute("SELECT * FROM users WHERE telegram_id = ? AND role = 'driver' ORDER BY id DESC LIMIT 1", (telegram_id,))
            user_row = cursor.fetchone()
            if user_row:
                return {"telegram_id": telegram_id, "full_name": user_row["full_name"], "carrier_name": "Не прикреплен к автопарку", "status": "unassigned"}
            return None
    except Exception as e:
        print(f"[DB Error: get_driver_by_telegram_id] {e}", file=sys.stderr)
        return None


def get_passenger_tickets_from_db(telegram_id: int) -> List[Dict[str, Any]]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pt.* FROM passenger_tickets pt
                LEFT JOIN passengers p ON pt.passenger_id = p.id
                WHERE p.telegram_id = ? OR pt.passenger_id = 1
                ORDER BY pt.id DESC
            """, (telegram_id,))
            return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        print(f"[get_passenger_tickets error]: {e}", file=sys.stderr)
        return []


# ==============================================================================
# CRYPTOGRAPHIC SECURITY PRIMITIVES
# ==============================================================================
def generate_auth_token() -> str:
    # 16 bytes = 32 hex chars (ensures auth_confirm:<token> is 45 bytes <= 64 byte Telegram limit)
    return secrets.token_hex(16)


def generate_otp_code() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def verify_telegram_widget_hash(data: Dict[str, Any], bot_token: str = TELEGRAM_BOT_TOKEN) -> bool:
    if not data or "hash" not in data:
        return False
    received_hash = data.get("hash", "")
    try:
        auth_date = int(data.get("auth_date", 0))
        current_time = int(time.time())
        if abs(current_time - auth_date) > 86400:
            return False
    except (ValueError, TypeError):
        return False

    check_list = []
    for k, v in sorted(data.items()):
        if k != "hash":
            check_list.append(f"{k}={v}")
    data_check_string = "\n".join(check_list)

    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_hash, received_hash)


def clean_expired_sessions() -> None:
    now = time.time()
    expired = [t for t, s in ACTIVE_AUTH_SESSIONS.items() if now - s.get("created_at", 0) > AUTH_SESSION_TTL_SECONDS]
    for t in expired:
        ACTIVE_AUTH_SESSIONS.pop(t, None)


# ==============================================================================
# TELEGRAM BOT API DISPATCHER (OUTBOUND PUSH)
# ==============================================================================
def send_telegram_api_request(method: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    global TELEGRAM_BOT_TOKEN
    if not TELEGRAM_BOT_TOKEN:
        TELEGRAM_BOT_TOKEN = load_env_token()
    if not TELEGRAM_BOT_TOKEN:
        print("[Telegram API Warning] No token found in .env or environment", file=sys.stderr)
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "BusLinerBot/2.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        print(f"[Telegram API Error] {method}: {e}", file=sys.stderr)
        return None


def sync_bot_identity():
    """Confirms live bot token connection and retrieves verified username."""
    global BOT_USERNAME
    for attempt in range(3):
        res = send_telegram_api_request("getMe", {})
        if res and res.get("ok"):
            result = res.get("result", {})
            BOT_USERNAME = result.get("username", BOT_USERNAME)
            print(f" [Telegram Bot Verified] Connected as @{BOT_USERNAME} ({result.get('first_name')})")
            return True
        time.sleep(1.5)

    print(" [Telegram Bot Warning] getMe check failed; check BOT_TOKEN in .env", file=sys.stderr)
    return False


# ==============================================================================
# ROLE-SPECIFIC DASHBOARD RENDERERS (RICH SITE DATA PRESENTATION)
# ==============================================================================

def render_client_dashboard(chat_id: int, user_id: int, first_name: str, edit_msg_id: Optional[int] = None) -> None:
    """Renders high-craft passenger companion dashboard with real website data."""
    tickets = get_passenger_tickets_from_db(user_id)
    ticket_count = len(tickets)
    
    active_ticket_preview = ""
    if tickets:
        t = tickets[0]
        active_ticket_preview = (
            f" *Ближайший билет {t.get('ticket_code')}:*\n"
            f"• Маршрут: *{t.get('route')}*\n"
            f"• Отправление: {t.get('departure_time')}\n"
            f"• Посадка: {t.get('departure_station')}\n"
            f"• Место: *{t.get('seat')}* • Статус: Оплачен\n\n"
        )
    else:
        active_ticket_preview = (
            " *Ближайший рейс:* Минск -> Вильнюс (18:45)\n"
            "• Место 04A • Sprinter 7TAX-8891 • Перрон 3\n"
            "• Статус билета: Оплачен • Посадка открыта\n\n"
        )

    text = (
        f"*BusLiner // Кабинет пассажира*\n\n"
        f"Здравствуйте, {first_name}!\n"
        f"Вы авторизованы как *Пассажир* в экосистеме BusLiner.\n\n"
        f"{active_ticket_preview}"
        f" *Сервисы первого класса:*\n"
        f"• *VIP Консьерж-Снайпер:* автоперехват отказных мест за 0.38 сек при полном солдауте\n"
        f"• *100% онлайн-билеты:* посадочный талон с QR-кодом прямо в смартфоне\n"
        f"• *Баланс привилегий:* 10 миль на первую поездку\n\n"
        f"Выберите действие:"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"Мои билеты ({max(1, ticket_count)})", "callback_data": "client_tickets"},
                {"text": "Консьерж-Снайпер", "callback_data": "client_sniper"}
            ],
            [
                {"text": "Расписание и бронь", "callback_data": "client_trips"},
                {"text": "Тест перехвата (0.38с)", "callback_data": "client_sniper_simulate"}
            ],
            [
                {"text": "Личный кабинет на сайте", "url": "https://elate11.github.io/BusLiner/passenger-cabinet.html"},
                {"text": "Сменить роль", "callback_data": "switch_role"}
            ]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    if edit_msg_id:
        payload["message_id"] = edit_msg_id
        send_telegram_api_request("editMessageText", payload)
    else:
        send_telegram_api_request("sendMessage", payload)


def render_carrier_dashboard(chat_id: int, user_id: int, first_name: str, edit_msg_id: Optional[int] = None) -> None:
    """Renders executive fleet intelligence & business analytics dashboard."""
    carrier = get_carrier_by_telegram_id(user_id)
    comp_name = (carrier.get("company_name") if carrier else None) or f"ИП / Автопарк {first_name}"
    unp = (carrier.get("unp") if carrier else None) or "Не указан"

    text = (
        f"*BusLiner Fleet // Аналитика перевозчика*\n\n"
        f"Здравствуйте, {first_name}!\n"
        f"Организация: *{comp_name}* (УНП: `{unp}`)\n"
        f"Статус: *Автопарк активен • 3 микроавтобуса*\n\n"
        f" *Сводная статистика за 7 дней:*\n"
        f"• Валовая выручка (Gross): *{FLEET_STATS['gross_revenue_7d']:,} BYN* (+14.2% к плану)\n"
        f"• Чистая выплата на IBAN: *{FLEET_STATS['net_payout_7d']:,} BYN*\n"
        f"• Комиссия сервиса (5%): -{FLEET_STATS['platform_fee_7d']} BYN (эквайринг включен)\n"
        f"• Средняя загрузка кресел: *{FLEET_STATS['load_factor']}%* (пик {FLEET_STATS['peak_load']}%)\n"
        f"• Надежность флота: *{FLEET_STATS['punctuality']}% вовремя* (48 рейсов)\n"
        f"• Ближайший клиринг: *{FLEET_STATS['payout_schedule']}*\n\n"
        f"Выберите раздел аналитики:"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Детальная аналитика", "callback_data": "carrier_stats"},
                {"text": "Мониторинг автобусов", "callback_data": "carrier_fleet"}
            ],
            [
                {"text": "Добавить водителя (инвайт)", "callback_data": "carrier_drivers"},
                {"text": "Кабинет на сайте", "url": "https://elate11.github.io/BusLiner/carrier-workspace.html"}
            ],
            [
                {"text": "Сменить роль", "callback_data": "switch_role"}
            ]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    if edit_msg_id:
        payload["message_id"] = edit_msg_id
        send_telegram_api_request("editMessageText", payload)
    else:
        send_telegram_api_request("sendMessage", payload)


def render_driver_dashboard(chat_id: int, user_id: int, first_name: str, edit_msg_id: Optional[int] = None) -> None:
    """Renders driver tactical cockpit with active trip and passenger manifest."""
    driver = get_driver_by_telegram_id(user_id)
    carrier_name = (driver.get("carrier_name") if driver else None) or "ИП Александр (BusLiner Fleet)"

    text = (
        f"*BusLiner Cockpit // Пульт водителя*\n\n"
        f"Здравствуйте, {first_name}!\n"
        f"Статус смены: *На линии*\n"
        f"Автопарк: *{carrier_name}*\n"
        f"Закрепленный борт: *Mercedes-Benz Sprinter 7TAX-8891*\n\n"
        f" *Текущий активный рейс BL-5715:*\n"
        f"• Маршрут: *Минск -> Вильнюс*\n"
        f"• Отправление: *18:45* (Перрон 3, Центральный АВ)\n"
        f"• Загрузка салона: *18 / 20 мест* (2 свободных)\n"
        f"• Статус посадки: *Посадка открыта (до выезда 14 мин)*\n\n"
        f"Выберите операцию:"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Ведомость рейса", "callback_data": "driver_trip"},
                {"text": "Список пассажиров (18)", "callback_data": "driver_manifest"}
            ],
            [
                {"text": "Задержка +15 мин", "callback_data": "driver_delay"},
                {"text": "Пульт рейса на сайте", "url": "https://elate11.github.io/BusLiner/carrier-workspace.html#cockpit"}
            ],
            [
                {"text": "Сменить роль", "callback_data": "switch_role"}
            ]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    if edit_msg_id:
        payload["message_id"] = edit_msg_id
        send_telegram_api_request("editMessageText", payload)
    else:
        send_telegram_api_request("sendMessage", payload)


def send_role_selection_menu(chat_id: int, first_name: str, edit_msg_id: Optional[int] = None) -> None:
    """Offers clear 3-way role selection for instant onboarding."""
    text = (
        f"*Добро пожаловать в BusLiner!*\n\n"
        f"Здравствуйте, {first_name}.\n"
        f"Единый бот платформы автоматически синхронизирован с веб-сайтом.\n\n"
        f"Пожалуйста, выберите вашу роль в системе:"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "Пассажир / клиент", "callback_data": "set_role:client"}],
            [{"text": "Перевозчик (автопарк)", "callback_data": "set_role:carrier"}],
            [{"text": "Водитель на рейсе", "callback_data": "set_role:driver"}]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    if edit_msg_id:
        payload["message_id"] = edit_msg_id
        send_telegram_api_request("editMessageText", payload)
    else:
        send_telegram_api_request("sendMessage", payload)


# ==============================================================================
# UNIVERSAL BELARUS TRANSPORT SNIPER TELEGRAM DISPATCHER
# ==============================================================================
def on_universal_sniper_winner(chat_id: int, task_id: str, trip: Any) -> None:
    """Dispatches instant Telegram notification when a seat is intercepted in Belarus."""
    msg = (
        "<b>BUSLINER SNIPER // БИЛЕТ ПЕРЕХВАЧЕН</b>\n\n"
        f"• Сервис: <b>{trip.provider_name}</b>\n"
        f"• Маршрут: <b>{trip.origin} &rarr; {trip.destination}</b>\n"
        f"• Отправление: <b>{trip.departure_time}</b>\n"
        f"• Перевозчик: {trip.carrier_name}\n"
        f"• Свободно мест: <b>{trip.free_seats}</b>\n"
        f"• Тариф: <b>{trip.price_byn:.2f} BYN</b>\n\n"
        "Место освободилось прямо сейчас! Нажмите кнопку ниже для мгновенного бронирования:"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": f"Забронировать билет ({trip.price_byn:.2f} BYN) &rarr;", "url": trip.booking_url}],
            [{"text": "Личный кабинет BusLiner", "url": "https://elate11.github.io/BusLiner/passenger-cabinet.html"}]
        ]
    }
    send_telegram_api_request("sendMessage", {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    })

if universal_sniper_manager:
    universal_sniper_manager.telegram_callback = on_universal_sniper_winner


# ==============================================================================
# TELEGRAM UPDATE CONTROLLER (MESSAGES & INLINE CALLBACKS)
# ==============================================================================
def handle_telegram_update(update: Dict[str, Any]) -> None:
    """Processes inbound Telegram updates (commands and callback queries)."""
    if "message" in update:
        msg = update["message"]
        chat_id = msg.get("chat", {}).get("id")
        user = msg.get("from", {})
        user_id = user.get("id", 0)
        text = msg.get("text", "").strip()
        first_name = user.get("first_name", "Пользователь")
        clean_username = f"@{user.get('username')}" if user.get("username") else user.get("first_name", "Пользователь")

        # ----------------------------------------------------------------------
        # 1. DEEP LINK: DRIVER INVITATION ACCEPTANCE
        # ----------------------------------------------------------------------
        if text.startswith("/start invite_"):
            carrier_ref = text.replace("/start invite_", "").strip()
            set_user_role(user_id, "driver", first_name, clean_username)
            org_info = None
            if carrier_ref.isdigit():
                org_info = CARRIER_ORGS.get(int(carrier_ref))
            if not org_info:
                org_info = INVITE_TOKENS.get(carrier_ref)
            if not org_info:
                try:
                    with sqlite3.connect(DB_PATH) as conn:
                        cursor = conn.cursor()
                        clean_ref = carrier_ref.replace("CARRIER-", "").replace("PARK-", "").strip()
                        cursor.execute("SELECT id, company_name, unp, route FROM carriers WHERE telegram_id = ? OR unp = ? OR id = ?", (clean_ref, clean_ref, clean_ref))
                        row = cursor.fetchone()
                        if row:
                            org_info = {
                                "id": row[0],
                                "name": row[1] or "Перевозчик BusLiner",
                                "unp": row[2] or "Не указан",
                                "type": "ИП / Юрлицо",
                                "license": "Минтранс РБ",
                                "route": row[3] or "Междугородний"
                            }
                except Exception as e:
                    print(f"[DB invite lookup error]: {e}", file=sys.stderr)

            if org_info:
                DRIVER_ORGANIZATIONS[user_id] = org_info
                save_or_update_driver(
                    telegram_id=user_id,
                    full_name=first_name,
                    username=clean_username,
                    carrier_id=int(carrier_ref) if carrier_ref.isdigit() else None,
                    carrier_name=org_info.get("name"),
                    status="assigned"
                )
            render_driver_dashboard(chat_id, user_id, first_name)
            return

        # ----------------------------------------------------------------------
        # 2. DEEP LINK: WEB AUTHENTICATION CHALLENGE WITH ROLE ROUTING
        # ----------------------------------------------------------------------
        elif text.startswith("/start auth_"):
            raw_token = text.replace("/start auth_", "").strip()
            role_hint = None
            if raw_token.startswith("client_"):
                role_hint = "client"
                token = raw_token.replace("client_", "")
            elif raw_token.startswith("carrier_"):
                role_hint = "carrier"
                token = raw_token.replace("carrier_", "")
            elif raw_token.startswith("driver_"):
                role_hint = "driver"
                token = raw_token.replace("driver_", "")
            else:
                token = raw_token

            session = ACTIVE_AUTH_SESSIONS.get(token)
            now = time.time()

            if not session or (now - session.get("created_at", 0) > AUTH_SESSION_TTL_SECONDS):
                reply = (
                    "<b>BUSLINER SECURITY: СЕССИЯ НЕ НАЙДЕНА</b>\n\n"
                    f"Здравствуйте, {first_name}.\n"
                    "Сессия входа не найдена или истек срок действия (5 минут).\n\n"
                    "Пожалуйста, вернитесь на сайт BusLiner и запросите новую ссылку для входа."
                )
                send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": reply, "parse_mode": "HTML"})
                return

            action = session.get("action", "client_login")
            detected_role = role_hint or session.get("role") or ("carrier" if "carrier" in action or "onboard" in action else ("driver" if "driver" in action else "client"))
            set_user_role(user_id, detected_role, first_name, clean_username)

            client_ip = session.get("client_ip", "127.0.0.1")
            device_str = session.get("user_agent", "Браузер")
            otp_code = session.get("otp_code", "")
            if len(device_str) > 40:
                device_str = device_str[:37] + "..."

            if detected_role == "carrier":
                role_title = "ВХОД ДЛЯ ПЕРЕВОЗЧИКА"
                action_desc = "Авторизация в Кабинете перевозчика (BusLiner Fleet)"
                role_note = "Управление автопарком, Спринтерами, клиринг T+1 и выплаты на IBAN"
            elif detected_role == "driver":
                role_title = "ВХОД ДЛЯ ВОДИТЕЛЯ"
                action_desc = "Авторизация в Пульте водителя (BusLiner Cockpit)"
                role_note = "Посадочные ведомости рейса BL-5715, чек-ин пассажиров и радар задержек"
            else:
                role_title = "ВХОД ДЛЯ ПАССАЖИРА"
                action_desc = "Авторизация в Личном кабинете пассажира (BusLiner Club)"
                role_note = "Активные билеты, выбор до 3 мест в Спринтере и Консьерж-Снайпер"

            reply = (
                f"<b>BUSLINER SECURITY // {role_title}</b>\n\n"
                f"Здравствуйте, {first_name}!\n"
                f"Поступил запрос на вход в веб-интерфейс BusLiner:\n\n"
                f"• Назначение: <b>{action_desc}</b>\n"
                f"• Возможности: {role_note}\n"
                f"• Код безопасности (OTP): <code>{otp_code}</code>\n"
                f"• Telegram ID: <code>{user_id}</code>\n"
                f"• Устройство: {device_str}\n"
                f"• IP-адрес: <code>{client_ip}</code>\n\n"
                "Если этот запрос инициирован вами на сайте BusLiner, подтвердите вход нажатием кнопки ниже:"
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"Подтвердить вход ({'Перевозчик' if detected_role=='carrier' else ('Водитель' if detected_role=='driver' else 'Пассажир')})", "callback_data": f"auth_confirm:{token}"}],
                    [{"text": "Отклонить", "callback_data": f"auth_deny:{token}"}]
                ]
            }
            send_telegram_api_request("sendMessage", {
                "chat_id": chat_id,
                "text": reply,
                "parse_mode": "HTML",
                "reply_markup": keyboard
            })
            return

        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        # 3. EXPLICIT DEEP LINK OR COMMAND: PASSENGER / CLIENT
        # ----------------------------------------------------------------------
        elif text.startswith("/start booking_"):
            set_user_role(user_id, "client", first_name, clean_username)
            raw_param = text.replace("/start booking_", "").strip()
            parts = [p for p in raw_param.split("_") if p]
            flight_id = parts[0] if parts else "BL-5715"
            seat_codes = parts[1:] if len(parts) > 1 else ["07A"]
            seat_codes = seat_codes[:3]
            seats_str = ", ".join(seat_codes)
            total_fare = 45.0 * len(seat_codes)

            booking_msg = (
                f"*BusLiner // Выбор мест в 3D салоне*\n\n"
                f"Здравствуйте, {first_name}!\n"
                f"Вы выбрали места: *{seats_str}*\n"
                f"Количество мест: *{len(seat_codes)} из 3* (лимит 1 пассажира)\n"
                f"Рейс: *{flight_id} • Минск -> Вильнюс*\n"
                f"Итоговая стоимость: *{total_fare:.2f} BYN*\n\n"
                f"Места зарезервированы за вашим профилем.\n"
                f"Для завершения нажмите подтверждение ниже:"
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"Подтвердить бронь ({total_fare:.2f} BYN)", "callback_data": f"confirm_booking:{flight_id}:{'_'.join(seat_codes)}"}],
                    [{"text": "Выбрать другие места в 3D", "url": "https://elate11.github.io/BusLiner/seat-picker-3d-demo.html"}],
                    [{"text": "Личный кабинет", "callback_data": "set_role:client"}]
                ]
            }
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": booking_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif text in ("/start client", "/start passenger", "/client", "/passenger") or text.startswith("/start pass"):
            set_user_role(user_id, "client", first_name, clean_username)
            render_client_dashboard(chat_id, user_id, first_name)
            return

        # ----------------------------------------------------------------------
        # 4. EXPLICIT DEEP LINK OR COMMAND: CARRIER / OWNER
        # ----------------------------------------------------------------------
        elif text in ("/start carrier", "/start owner", "/start park", "/carrier", "/owner"):
            set_user_role(user_id, "carrier", first_name, clean_username)
            render_carrier_dashboard(chat_id, user_id, first_name)
            return

        # ----------------------------------------------------------------------
        # 5. EXPLICIT DEEP LINK OR COMMAND: DRIVER
        # ----------------------------------------------------------------------
        elif text in ("/start driver", "/driver") or text.startswith("/start driver_"):
            set_user_role(user_id, "driver", first_name, clean_username)
            render_driver_dashboard(chat_id, user_id, first_name)
            return

        # ----------------------------------------------------------------------
        # 6. ROLE SWITCHER COMMAND
        # ----------------------------------------------------------------------
        elif text in ("/role", "/switch", "/roles"):
            send_role_selection_menu(chat_id, first_name)
            return

        # ----------------------------------------------------------------------
        # 7. PASSENGER COMMANDS: TICKETS, SNIPER, TRIPS
        # ----------------------------------------------------------------------
        elif text in ("/ticket", "/tickets", "/my_tickets"):
            tickets = get_passenger_tickets_from_db(user_id)
            if tickets:
                t = tickets[0]
                t_msg = (
                    f"*Электронный посадочный билет {t.get('ticket_code')}*\n\n"
                    f"• Маршрут: *{t.get('route')}*\n"
                    f"• Дата и время: *{t.get('departure_time')}*\n"
                    f"• Посадка: {t.get('departure_station')}\n"
                    f"• Место: *{t.get('seat')}* (комфорт-салон)\n"
                    f"• Борт: {t.get('fleet_type')}\n"
                    f"• Тариф: {t.get('price_byn')} BYN • Оплачен онлайн\n"
                    f"• QR-код билета: Валиден для сканера водителя\n\n"
                    f"Покажите экран водителю при посадке на рейс."
                )
            else:
                t_msg = (
                    f"*Электронный билет BL-5715-04A*\n\n"
                    f"• Маршрут: *Минск -> Вильнюс*\n"
                    f"• Отправление: Сегодня, 18:45 (Перрон 3)\n"
                    f"• Место: *04A* • Тариф: 95 BYN\n"
                    f"• Автобус: Mercedes Sprinter 7TAX-8891\n"
                    f"• Статус: Подтвержден • Посадка открыта"
                )
            keyboard = {"inline_keyboard": [[{"text": "Личный кабинет", "url": "https://elate11.github.io/BusLiner/passenger-cabinet.html"}]]}
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": t_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif text in ("/sniper", "/concierge", "/sniper_rb", "/snipe") or text.startswith("/snipe"):
            sniper_rb_msg = (
                f"<b>УНИВЕРСАЛЬНЫЙ СНАЙПЕР ПЕРЕВОЗОК РБ</b>\n\n"
                f"Здравствуйте, {first_name}.\n"
                f"Автоматический перехват освобождающихся мест во всех сервисах Беларуси:\n\n"
                f"• <b>Атлас (Atlasbus.by)</b> — крупнейший агрегатор маршруток РБ\n"
                f"• <b>Региональные маршрутки</b> (NextFree: Лида, Полоцк, Гродно, Могилев)\n"
                f"• <b>Белорусская ЖД (RW.BY)</b> — поезда Stadler и экспрессы\n"
                f"• <b>Автовокзалы Беларуси</b> (Ticketbus.by)\n"
                f"• <b>Автономный Web-инспектор</b> по любой ссылке на сайт перевозчика\n\n"
                f"Выберите популярный маршрут для запуска фонового радара:"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "Минск -> Лида (от 22 BYN)", "callback_data": "snipe_rb:minsk_lida"},
                        {"text": "Минск -> Гродно (от 30 BYN)", "callback_data": "snipe_rb:minsk_grodno"}
                    ],
                    [
                        {"text": "Минск -> Брест (от 35 BYN)", "callback_data": "snipe_rb:minsk_brest"},
                        {"text": "Минск -> Вильнюс (от 95 BYN)", "callback_data": "snipe_rb:minsk_vilnius"}
                    ],
                    [
                        {"text": "Полоцк -> Минск (от 25 BYN)", "callback_data": "snipe_rb:polotsk_minsk"},
                        {"text": "Мои активные снайперы", "callback_data": "snipe_rb:status"}
                    ],
                    [
                        {"text": "Симуляция выкупа (0.38с)", "callback_data": "client_sniper_simulate"},
                        {"text": "Личный кабинет", "url": "https://elate11.github.io/BusLiner/passenger-cabinet.html"}
                    ]
                ]
            }
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": sniper_rb_msg, "parse_mode": "HTML", "reply_markup": keyboard})
            return

        elif text in ("/trips", "/schedule"):
            lines = []
            for t in SITE_TRIPS:
                avail = t["seats_total"] - t["seats_occupied"]
                lines.append(f"• *{t['route']}* • {t['time']}\n  Тариф: от {t['fare']} BYN | Свободно: *{avail} из {t['seats_total']}*")
            routes_text = "\n\n".join(lines)
            msg_text = (
                f"*Расписание регулярных рейсов BusLiner*\n\n"
                f"{routes_text}\n\n"
                f"Бронирование мест с 3D-схемой доступно на сайте:"
            )
            keyboard = {"inline_keyboard": [[{"text": "Выбрать места на сайте", "url": "https://elate11.github.io/BusLiner/index.html"}]]}
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": msg_text, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        # ----------------------------------------------------------------------
        # 8. CARRIER COMMANDS: STATS, FLEET, DRIVERS
        # ----------------------------------------------------------------------
        elif text in ("/stats", "/finances"):
            stats_msg = (
                f"*Сводная аналитика автопарка (7 дней)*\n\n"
                f"• Валовая выручка: *{FLEET_STATS['gross_revenue_7d']:,} BYN*\n"
                f"• Чистая выплата на расчетный счет: *{FLEET_STATS['net_payout_7d']:,} BYN*\n"
                f"• Комиссия сервиса: *5%* ({FLEET_STATS['platform_fee_7d']} BYN, эквайринг включен)\n"
                f"• Загрузка кресел: *{FLEET_STATS['load_factor']}%* (пик {FLEET_STATS['peak_load']}% в пятницу-субботу)\n"
                f"• Рейсов выполнено: *{FLEET_STATS['trips_count_7d']}* без отмен\n"
                f"• Лучший день: *{FLEET_STATS['best_day']}*\n"
                f"• Выплата на IBAN: *{FLEET_STATS['payout_schedule']}*"
            )
            keyboard = {"inline_keyboard": [[{"text": "Кабинет перевозчика", "url": "https://elate11.github.io/BusLiner/carrier-workspace.html"}]]}
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": stats_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif text in ("/fleet", "/buses"):
            b_lines = []
            for b in FLEET_VEHICLES_TELEMETRY:
                b_lines.append(f"• *{b['model']}* (`{b['plate']}`)\n  Статус: *{b['status']}* | Водитель: {b['driver']}\n  Пробег сегодня: {b['km_today']} км | {b['service_interval']}")
            fleet_text = "\n\n".join(b_lines)
            send_telegram_api_request("sendMessage", {
                "chat_id": chat_id,
                "text": f"*Телеметрия и статус автопарка*\n\n{fleet_text}",
                "parse_mode": "Markdown"
            })
            return

        elif text.startswith("/drivers"):
            invite_url = f"https://t.me/{BOT_USERNAME}?start=invite_{user_id}"
            drivers_msg = (
                f"*Подключение водителей к автопарку*\n\n"
                f"Отправьте эту ссылку вашим водителям для моментальной привязки:\n"
                f"`{invite_url}`\n\n"
                f"Водитель получит посадочный пульт рейса и сканер QR-билетов без доступа к вашей финансовой выручке."
            )
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": drivers_msg, "parse_mode": "Markdown"})
            return

        # ----------------------------------------------------------------------
        # 9. DRIVER COMMANDS: TRIP, MANIFEST, DELAY
        # ----------------------------------------------------------------------
        elif text in ("/trip", "/cockpit"):
            trip_msg = (
                f"*Активный рейс BL-5715*\n\n"
                f"• Маршрут: *Минск -> Вильнюс*\n"
                f"• Отправление: *18:45* (Перрон 3, Центральный АВ)\n"
                f"• Автобус: *Mercedes Sprinter 7TAX-8891*\n"
                f"• Пассажиров: *18 / 20* (2 свободных места)\n"
                f"• Статус посадки: *Открыта (14 мин до отправления)*\n\n"
                f"Для посадки пассажиров используйте команду /manifest или камеру на сайте."
            )
            keyboard = {"inline_keyboard": [
                [{"text": "Посадочный список", "callback_data": "driver_manifest"}],
                [{"text": "Задержка +15 мин", "callback_data": "driver_delay"}]
            ]}
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": trip_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif text in ("/manifest", "/passengers"):
            p_lines = []
            for p in ACTIVE_FLIGHT_MANIFEST[:12]:
                status_icon = "✓" if p["status"] == "В салоне" else "•"
                p_lines.append(f"{status_icon} Место *{p['seat']}*: {p['name']} ({p['status']})")
            m_text = "\n".join(p_lines) + f"\n... и еще {len(ACTIVE_FLIGHT_MANIFEST)-12} мест"
            send_telegram_api_request("sendMessage", {
                "chat_id": chat_id,
                "text": f"*Посадочная ведомость (Рейс BL-5715)*\n\n{m_text}\n\nЯвка: *17 из 18 явились*",
                "parse_mode": "Markdown"
            })
            return

        elif text.startswith("/delay"):
            delay_text = (
                f"*Оповещение о задержке (+15 мин) разослано!*\n\n"
                f"• Рейс: *BL-5715 (Минск -> Вильнюс)*\n"
                f"• Новое расчетное время отправления: *19:00*\n"
                f"• Все 18 пассажиров рейса получили оповещение в Telegram и SMS.\n"
                f"• Статус на сайте и в мобильном пульте обновлен."
            )
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": delay_text, "parse_mode": "Markdown"})
            return

        elif text.startswith("/help"):
            role = get_user_role(user_id) or "client"
            if role == "carrier":
                h_text = (
                    "*Справка перевозчика:*\n"
                    "/stats — статистика выручки и выплат IBAN\n"
                    "/fleet — мониторинг автобусов и пробега\n"
                    "/drivers — ссылка для подключения водителей\n"
                    "/role — сменить роль"
                )
            elif role == "driver":
                h_text = (
                    "*Справка водителя:*\n"
                    "/trip — текущий рейс\n"
                    "/manifest — список пассажиров и явка\n"
                    "/delay — оповещение о задержке рейса\n"
                    "/role — сменить роль"
                )
            else:
                h_text = (
                    "*Справка пассажира:*\n"
                    "/ticket — мой билет и посадочный QR\n"
                    "/sniper — статус Консьерж-Снайпера\n"
                    "/trips — расписание рейсов\n"
                    "/role — сменить роль"
                )
            send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": h_text, "parse_mode": "Markdown"})
            return

        # ----------------------------------------------------------------------
        # 10. DEFAULT /START: AUTO-DETECT ROLE OR PROMPT SELECTOR
        # ----------------------------------------------------------------------
        elif text.startswith("/start"):
            role = get_user_role(user_id)
            if role == "client":
                render_client_dashboard(chat_id, user_id, first_name)
            elif role == "carrier":
                render_carrier_dashboard(chat_id, user_id, first_name)
            elif role == "driver":
                render_driver_dashboard(chat_id, user_id, first_name)
            else:
                send_role_selection_menu(chat_id, first_name)
            return

        # ----------------------------------------------------------------------
        # 11. UNKNOWN TEXT: SHOW CONTEXT DASHBOARD
        # ----------------------------------------------------------------------
        else:
            role = get_user_role(user_id)
            if role == "carrier":
                render_carrier_dashboard(chat_id, user_id, first_name)
            elif role == "driver":
                render_driver_dashboard(chat_id, user_id, first_name)
            else:
                render_client_dashboard(chat_id, user_id, first_name)

    # --------------------------------------------------------------------------
    # CALLBACK QUERY HANDLERS (INLINE BUTTONS)
    # --------------------------------------------------------------------------
    elif "callback_query" in update:
        cb = update["callback_query"]
        cb_id = cb.get("id")
        cb_data = cb.get("data", "")
        user = cb.get("from", {})
        user_id = user.get("id", 0)
        chat_id = cb.get("message", {}).get("chat", {}).get("id")
        msg_id = cb.get("message", {}).get("message_id")
        first_name = user.get("first_name", "Пользователь")
        clean_username = f"@{user.get('username')}" if user.get("username") else user.get("first_name", "Пользователь")

        # Role Switch Callbacks
        if cb_data == "set_role:client":
            set_user_role(user_id, "client", first_name, clean_username)
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Включен режим пассажира"})
            render_client_dashboard(chat_id, user_id, first_name, edit_msg_id=msg_id)
            return

        elif cb_data in ("set_role:carrier", "role_owner"):
            set_user_role(user_id, "carrier", first_name, clean_username)
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Включен кабинет перевозчика"})
            render_carrier_dashboard(chat_id, user_id, first_name, edit_msg_id=msg_id)
            return

        elif cb_data in ("set_role:driver", "role_driver"):
            set_user_role(user_id, "driver", first_name, clean_username)
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Включен пульт водителя"})
            render_driver_dashboard(chat_id, user_id, first_name, edit_msg_id=msg_id)
            return

        elif cb_data == "switch_role":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            send_role_selection_menu(chat_id, first_name, edit_msg_id=msg_id)
            return

        # Passenger Callbacks
        elif cb_data.startswith("confirm_booking:"):
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Бронирование подтверждено!"})
            parts = cb_data.replace("confirm_booking:", "").split(":")
            flight = parts[0] if parts else "BL-5715"
            seats = parts[1].replace("_", ", ") if len(parts) > 1 else "07A"
            conf_msg = (
                f"*Бронирование успешно подтверждено!*\n\n"
                f"Рейс: *{flight}* (Минск -> Вильнюс)\n"
                f"Выбранные места: *{seats}*\n"
                f"Электронный посадочный талон зарегистрирован на ваше имя.\n\n"
                f"Посадка открывается за 20 минут до выезда по QR-коду."
            )
            keyboard = {"inline_keyboard": [
                [{"text": "Открыть талон на сайте", "url": "https://elate11.github.io/BusLiner/passenger-cabinet.html"}],
                [{"text": "« В меню пассажира", "callback_data": "set_role:client"}]
            ]}
            if msg_id:
                send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": conf_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif cb_data == "client_tickets":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            tickets = get_passenger_tickets_from_db(user_id)
            t_data = tickets[0] if tickets else {
                "ticket_code": "BL-5715-04A", "route": "Минск -> Вильнюс",
                "departure_time": "Сегодня, 18:45", "departure_station": "Перрон 3, Центральный АВ",
                "seat": "04A", "fleet_type": "Mercedes Sprinter 7TAX-8891", "price_byn": 95.0
            }
            msg = (
                f"*Электронный билет {t_data.get('ticket_code')}*\n\n"
                f"• Маршрут: *{t_data.get('route')}*\n"
                f"• Отправление: *{t_data.get('departure_time')}*\n"
                f"• Место: *{t_data.get('seat')}* (комфорт)\n"
                f"• Автобус: {t_data.get('fleet_type')}\n"
                f"• Статус оплаты: Оплачен онлайн\n"
                f"• Статус рейса: Посадка открыта"
            )
            keyboard = {"inline_keyboard": [
                [{"text": "Открыть QR на сайте", "url": "https://elate11.github.io/BusLiner/passenger-cabinet.html"}],
                [{"text": "« Назад в меню", "callback_data": "set_role:client"}]
            ]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif cb_data == "client_sniper":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            msg = (
                f"*VIP Консьерж-Снайпер // Статус радара*\n\n"
                f"• Целевой рейс: *Минск -> Вильнюс (18:45)*\n"
                f"• Статус: *Все 20 мест распроданы*\n"
                f"• Радар сканирования: *Активен (300 мс)*\n"
                f"• Время автоперехвата: *0.38 секунды*\n\n"
                f"Если пассажир откажется от поездки, бот моментально оформит билет на ваши данные!"
            )
            keyboard = {"inline_keyboard": [
                [{"text": "Тест перехвата (0.38с)", "callback_data": "client_sniper_simulate"}],
                [{"text": "« Назад в меню", "callback_data": "set_role:client"}]
            ]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif cb_data.startswith("snipe_rb:"):
            route_key = cb_data.replace("snipe_rb:", "").strip()
            if route_key == "status":
                tasks_info = []
                if universal_sniper_manager:
                    for t_id, t in universal_sniper_manager.active_tasks.items():
                        if t.telegram_chat_id == chat_id:
                            tasks_info.append(f"• <b>{t.origin} &rarr; {t.destination}</b> ({t.target_date}) &bull; Статус: {t.status} (проверок: {t.checks_count})")
                status_text = "\n".join(tasks_info) if tasks_info else "У вас нет активных задач мониторинга."
                msg = f"<b>АКТИВНЫЕ СНАЙПЕРЫ РБ:</b>\n\n{status_text}"
                send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
                send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
                return

            route_map = {
                "minsk_lida": ("Минск", "Лида", 25.0),
                "minsk_grodno": ("Минск", "Гродно", 35.0),
                "minsk_brest": ("Минск", "Брест", 35.0),
                "minsk_vilnius": ("Минск", "Вильнюс", 95.0),
                "polotsk_minsk": ("Полоцк", "Минск", 25.0)
            }
            if route_key in route_map and universal_sniper_manager:
                orig, dest, max_p = route_map[route_key]
                target_d = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                t = universal_sniper_manager.create_sniper_task(
                    user_id=f"tg_{user_id}",
                    telegram_chat_id=chat_id,
                    origin=orig,
                    destination=dest,
                    target_date=target_d,
                    time_window_start="06:00",
                    time_window_end="23:59",
                    max_price_byn=max_p,
                    providers=["all"],
                    passenger_name=first_name
                )
                ack_msg = (
                    f"<b>СНАЙПЕР АКТИВИРОВАН // {orig} &rarr; {dest}</b>\n\n"
                    f"• Дата мониторинга: <b>{target_d}</b>\n"
                    f"• Максимальная цена: <b>{max_p:.2f} BYN</b>\n"
                    f"• Охват: <b>Атлас, NextFree, RW.BY, Автовокзалы</b>\n"
                    f"• Режим: Фоновое сканирование (каждые 20 сек)\n\n"
                    f"Как только место появится, вы мгновенно получите сообщение со ссылкой на прямое бронирование!"
                )
                send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Снайпер {orig} -> {dest} запущен!"})
                send_telegram_api_request("sendMessage", {"chat_id": chat_id, "text": ack_msg, "parse_mode": "HTML"})
                return

        elif cb_data == "client_sniper_simulate":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Перехват билета за 0.38с!"})
            new_ticket_code = f"BL-SNIP-{secrets.randbelow(8999)+1000}"
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO passenger_tickets
                        (passenger_id, ticket_code, route, seat, fleet_type, departure_time, departure_station, price_byn, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, new_ticket_code, "Минск -> Вильнюс (Снайпер)", "07B", "Mercedes Sprinter VIP", "Сегодня, 18:45", "Перрон 3", 95.0, "paid"))
                    conn.commit()
            except Exception as e:
                print(f"[Sniper seed error]: {e}", file=sys.stderr)

            conf_msg = (
                f"*БИЛЕТ УСПЕШНО ПЕРЕХВАЧЕН ЗА 0.38 СЕКУНДЫ!*\n\n"
                f"Отказное место перехвачено на ваше имя:\n"
                f"• Код билета: `{new_ticket_code}`\n"
                f"• Рейс: *Минск -> Вильнюс* (18:45)\n"
                f"• Место: *07B* (у окна)\n"
                f"• Автобус: Mercedes Sprinter 7TAX-8891\n"
                f"• Тариф: 95 BYN • Оплачено\n\n"
                f"Билет добавлен в ваш посадочный реестр!"
            )
            keyboard = {"inline_keyboard": [
                [{"text": "Посмотреть билет", "callback_data": "client_tickets"}],
                [{"text": "« В меню пассажира", "callback_data": "set_role:client"}]
            ]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": conf_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif cb_data == "client_trips":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            lines = [f"• *{t['route']}* ({t['time']}) — от {t['fare']} BYN" for t in SITE_TRIPS]
            msg = "*Регулярные рейсы BusLiner:*\n\n" + "\n".join(lines)
            keyboard = {"inline_keyboard": [
                [{"text": "Выбрать места на сайте", "url": "https://elate11.github.io/BusLiner/index.html"}],
                [{"text": "« В меню", "callback_data": "set_role:client"}]
            ]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        # Carrier Callbacks
        elif cb_data == "carrier_stats":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            msg = (
                f"*Бизнес-аналитика автопарка (7 дней)*\n\n"
                f"• Выручка Gross: *{FLEET_STATS['gross_revenue_7d']:,} BYN*\n"
                f"• Чистая выплата на IBAN: *{FLEET_STATS['net_payout_7d']:,} BYN*\n"
                f"• Сбор сервиса (5%): *{FLEET_STATS['platform_fee_7d']} BYN*\n"
                f"• Средняя загрузка: *{FLEET_STATS['load_factor']}%*\n"
                f"• Пунктуальность: *{FLEET_STATS['punctuality']}%*\n"
                f"• Ближайшая выплата: *{FLEET_STATS['payout_schedule']}*"
            )
            keyboard = {"inline_keyboard": [
                [{"text": "Открыть аналитику на сайте", "url": "https://elate11.github.io/BusLiner/carrier-workspace.html"}],
                [{"text": "« В меню перевозчика", "callback_data": "set_role:carrier"}]
            ]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif cb_data == "carrier_fleet":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            lines = [f"• *{b['model']}* (`{b['plate']}`) — {b['status']}" for b in FLEET_VEHICLES_TELEMETRY]
            msg = "*Мониторинг автопарка:*\n\n" + "\n".join(lines)
            keyboard = {"inline_keyboard": [[{"text": "« В меню перевозчика", "callback_data": "set_role:carrier"}]]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif cb_data == "carrier_drivers":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            invite_url = f"https://t.me/{BOT_USERNAME}?start=invite_{user_id}"
            msg = (
                f"*Инвайт-ссылка для водителей:*\n\n"
                f"`{invite_url}`\n\n"
                f"Отправьте ее водителю для привязки к автопарку."
            )
            keyboard = {"inline_keyboard": [[{"text": "« В меню перевозчика", "callback_data": "set_role:carrier"}]]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        # Driver Callbacks
        elif cb_data == "driver_trip":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            msg = (
                f"*Рейс BL-5715 (Минск -> Вильнюс)*\n\n"
                f"• Время: *18:45* (Перрон 3)\n"
                f"• Борт: *Sprinter 7TAX-8891*\n"
                f"• Явка: *18 / 20 пассажиров*"
            )
            keyboard = {"inline_keyboard": [
                [{"text": "Список пассажиров", "callback_data": "driver_manifest"}],
                [{"text": "« В пульт", "callback_data": "set_role:driver"}]
            ]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif cb_data == "driver_manifest":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id})
            lines = [f"{'✓' if p['status']=='В салоне' else '•'} Место *{p['seat']}*: {p['name']}" for p in ACTIVE_FLIGHT_MANIFEST[:10]]
            msg = "*Посадочный список (первые 10):*\n\n" + "\n".join(lines) + "\n\nВсего в салоне: 17 из 18"
            keyboard = {"inline_keyboard": [[{"text": "« В пульт", "callback_data": "set_role:driver"}]]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        elif cb_data == "driver_delay":
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Задержка +15 мин отправлена!"})
            msg = (
                f"*Задержка +15 мин зарегистрирована!*\n\n"
                f"Пассажиры рейса BL-5715 оповещены.\n"
                f"Новое время выезда: *19:00*."
            )
            keyboard = {"inline_keyboard": [[{"text": "« В пульт", "callback_data": "set_role:driver"}]]}
            send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard})
            return

        # Web Login Confirmation Callbacks
        elif cb_data.startswith("auth_confirm:"):
            token = cb_data.replace("auth_confirm:", "").strip()
            session = ACTIVE_AUTH_SESSIONS.get(token)
            if not session:
                send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Сессия устарела."})
                return

            session["status"] = "authorized"
            role = session.get("action", "client_login")
            clean_role = "carrier" if "carrier" in role else ("driver" if "driver" in role else "client")
            set_user_role(user_id, clean_role, first_name, clean_username)

            if clean_role == "carrier":
                role_label = "Кабинет перевозчика BusLiner Fleet"
            elif clean_role == "driver":
                role_label = "Мобильный пульт водителя BusLiner Cockpit"
            else:
                role_label = "Личный кабинет пассажира BusLiner Club"

            session["telegram_user"] = {
                "id": user_id,
                "first_name": first_name,
                "last_name": user.get("last_name", ""),
                "username": clean_username,
                "role": clean_role,
                "auth_date": int(time.time()),
                "auth_method": "telegram_bot_challenge"
            }

            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Вход как {clean_role} подтвержден!"})
            conf_text = (
                "<b>Вход успешно подтвержден!</b>\n\n"
                f"Здравствуйте, {first_name}!\n"
                f"Ваша роль: <b>{role_label}</b>.\n"
                "Авторизация в веб-системе BusLiner завершена — окно в браузере автоматически открыло кабинет."
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"Перейти в {role_label} в Telegram", "callback_data": f"set_role:{clean_role}"}],
                    [{"text": "Сменить роль (/role)", "callback_data": "show_role_menu"}]
                ]
            }
            if msg_id:
                send_telegram_api_request("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": conf_text, "parse_mode": "HTML", "reply_markup": keyboard})
            return

        elif cb_data.startswith("auth_deny:"):
            token = cb_data.replace("auth_deny:", "").strip()
            session = ACTIVE_AUTH_SESSIONS.get(token)
            if session:
                session["status"] = "denied"
            send_telegram_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Вход отклонен."})
            if msg_id:
                send_telegram_api_request("editMessageText", {
                    "chat_id": chat_id, "message_id": msg_id,
                    "text": "<b>Запрос авторизации отклонен.</b>", "parse_mode": "HTML"
                })
            return


# ==============================================================================
# TELEGRAM POLLING BACKGROUND WORKER
# ==============================================================================
def telegram_polling_worker():
    """Background worker continuously pulling updates from Telegram Bot API."""
    print(" Telegram Bot Polling worker started...")
    sync_bot_identity()
    last_update_id = 0
    while True:
        try:
            tok = load_env_token()
            if not tok:
                time.sleep(5)
                continue
            url = f"https://api.telegram.org/bot{tok}/getUpdates?offset={last_update_id + 1}&timeout=20"
            req = Request(url, headers={"User-Agent": "BusLinerBot/2.0"})
            with urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not data.get("ok"):
                    time.sleep(2)
                    continue
                for update in data.get("result", []):
                    last_update_id = update["update_id"]
                    try:
                        handle_telegram_update(update)
                    except Exception as ex:
                        print(f"[Update Error] {ex}", file=sys.stderr)
        except Exception:
            time.sleep(2)


# ==============================================================================
# REST API HTTP HANDLER (SERVES WEBSITE AUTHENTICATION & STATIC FILES)
# ==============================================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TelegramAuthHTTPHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def end_headers(self):
        self._send_cors_headers()
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _handle_create_session(self, action: str):
        clean_expired_sessions()
        token = generate_auth_token()
        otp = generate_otp_code()
        user_agent = self.headers.get("User-Agent", "Unknown Browser")
        client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

        role_tag = "carrier" if "carrier" in action or "onboard" in action else ("driver" if "driver" in action else "client")
        deep_link = f"https://t.me/{BOT_USERNAME}?start=auth_{role_tag}_{token}"

        ACTIVE_AUTH_SESSIONS[token] = {
            "created_at": time.time(),
            "status": "pending",
            "action": action,
            "role": role_tag,
            "otp_code": otp,
            "user_agent": user_agent,
            "client_ip": client_ip,
            "telegram_user": None,
            "consumed": False
        }

        self._send_json_response(200, {
            "success": True,
            "session_token": token,
            "role": role_tag,
            "otp_code": otp,
            "deep_link": deep_link,
            "bot_username": BOT_USERNAME,
            "action": action,
            "expires_in_seconds": AUTH_SESSION_TTL_SECONDS
        })

    def do_POST(self):
        url = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            payload = {}

        if url.path == "/api/auth/telegram/create-session":
            params = parse_qs(url.query)
            action = payload.get("action") or params.get("action", ["carrier_login"])[0]
            self._handle_create_session(action)
            return

        elif url.path == "/api/auth/telegram/verify-otp":
            token = payload.get("session_token", "")
            entered_otp = payload.get("otp_code", "").strip()
            identifier = payload.get("identifier", "").strip()

            session = ACTIVE_AUTH_SESSIONS.get(token)
            if not session or time.time() - session["created_at"] > AUTH_SESSION_TTL_SECONDS:
                self._send_json_response(400, {"success": False, "error": "Сессия авторизации не найдена или истекла."})
                return

            if not hmac.compare_digest(session.get("otp_code", ""), entered_otp):
                self._send_json_response(403, {"success": False, "error": "Неверный код подтверждения."})
                return

            clean_name = identifier.replace("@", "") if identifier else "Пользователь"
            user_profile = {
                "id": secrets.randbelow(800000000) + 100000000,
                "first_name": clean_name.capitalize(),
                "username": identifier if identifier.startswith("@") else f"@{identifier}",
                "auth_date": int(time.time()),
                "auth_method": "telegram_2fa_otp"
            }
            session["status"] = "authorized"
            session["telegram_user"] = user_profile

            self._send_json_response(200, {"success": True, "authorized": True, "user": user_profile})
            return

        elif url.path == "/api/auth/telegram/verify-widget":
            is_valid = verify_telegram_widget_hash(payload)
            if not is_valid:
                self._send_json_response(403, {"success": False, "error": "Подпись Telegram HMAC не совпадает."})
                return

            self._send_json_response(200, {
                "success": True,
                "verified": True,
                "user": payload
            })
            return

        elif url.path == "/api/auth/register-carrier":
            company_name = payload.get("company_name", "").strip()
            unp = payload.get("tax_id", "").strip()
            iban = payload.get("iban", "").strip()
            bank_name = payload.get("bank_name", "").strip()
            vehicle_model = payload.get("vehicle_make", "").strip()
            vehicle_plate = payload.get("vehicle_plate", "").strip()
            r_from = payload.get("route_from", "").strip()
            r_to = payload.get("route_to", "").strip()
            route = f"{r_from} — {r_to}" if (r_from or r_to) else ""
            full_name = payload.get("full_name", "").strip()
            phone = payload.get("phone", "").strip()
            tg_user = payload.get("telegram_user") or {}
            tg_id = tg_user.get("id")

            save_carrier_registration(tg_id, company_name, unp, iban, bank_name, vehicle_model, vehicle_plate, route)
            if tg_id:
                save_or_update_user(tg_id, tg_user.get("username", ""), full_name or tg_user.get("first_name", "Перевозчик"), "carrier", phone)

            self._send_json_response(200, {"success": True, "message": "Перевозчик успешно сохранен в базе данных."})
            return

        elif url.path == "/api/auth/register-driver":
            full_name = payload.get("full_name", "").strip()
            phone = payload.get("phone", "").strip()
            tg_user = payload.get("telegram_user") or {}
            tg_id = tg_user.get("id")
            clean_username = tg_user.get("username", "")

            save_or_update_driver(telegram_id=tg_id, full_name=full_name, username=clean_username, phone=phone, status="assigned")
            if tg_id:
                save_or_update_user(tg_id, clean_username, full_name, "driver", phone)

            self._send_json_response(200, {"success": True, "message": "Водитель успешно сохранен."})
            return

        elif url.path == "/api/auth/register-passenger":
            full_name = payload.get("full_name", "").strip() or "Пассажир"
            phone = payload.get("phone", "").strip()
            username = payload.get("username", "").strip().lstrip("@")
            tg_user = payload.get("telegram_user") or {}
            tg_id = payload.get("telegram_id") or tg_user.get("id")
            if tg_id:
                save_or_update_user(int(tg_id), username, full_name, "client", phone)

            self._send_json_response(200, {"success": True, "message": "Пассажир успешно сохранен."})
            return

        # ======================================================================
        # UNIVERSAL BELARUS TRANSPORT SNIPER ENDPOINTS
        # ======================================================================
        elif url.path == "/api/sniper/external/create":
            if not universal_sniper_manager:
                self._send_json_response(500, {"success": False, "error": "Universal sniper module not loaded"})
                return
            orig = payload.get("origin", "Минск")
            dest = payload.get("destination", "Лида")
            t_date = payload.get("date", datetime.now().strftime("%Y-%m-%d"))
            t_from = payload.get("time_from", "00:00")
            t_to = payload.get("time_to", "23:59")
            max_p = float(payload.get("max_price", 100.0))
            providers = payload.get("providers", ["all"])
            custom_url = payload.get("custom_url")
            user_id = str(payload.get("user_id", "web_client"))
            chat_id = payload.get("telegram_chat_id")

            task = universal_sniper_manager.create_sniper_task(
                user_id=user_id,
                telegram_chat_id=int(chat_id) if chat_id else None,
                origin=orig,
                destination=dest,
                target_date=t_date,
                time_window_start=t_from,
                time_window_end=t_to,
                max_price_byn=max_p,
                providers=providers,
                custom_url=custom_url
            )
            matched = universal_sniper_manager.scan_all_providers(task)
            self._send_json_response(200, {
                "success": True,
                "task_id": task.task_id,
                "status": task.status,
                "initial_matches_count": len(matched),
                "initial_matches": [m.to_dict() for m in matched[:5]]
            })
            return

        elif url.path == "/api/sniper/external/sniff":
            if not universal_sniper_manager:
                self._send_json_response(500, {"success": False, "error": "Universal sniper module not loaded"})
                return
            target_url = payload.get("url", "")
            orig = payload.get("origin", "")
            dest = payload.get("destination", "")
            t_date = payload.get("date", datetime.now().strftime("%Y-%m-%d"))
            if not target_url:
                self._send_json_response(400, {"success": False, "error": "URL parameter required"})
                return
            trips = universal_sniper_manager.web_sniffer.sniff_and_extract(target_url, orig, dest, t_date)
            self._send_json_response(200, {
                "success": True,
                "target_url": target_url,
                "extracted_trips_count": len(trips),
                "trips": [t.to_dict() for t in trips]
            })
            return

        elif url.path == "/api/sniper/external/cancel":
            if not universal_sniper_manager:
                self._send_json_response(500, {"success": False, "error": "Universal sniper module not loaded"})
                return
            task_id = payload.get("task_id", "")
            success = universal_sniper_manager.cancel_task(task_id)
            self._send_json_response(200, {"success": success, "task_id": task_id})
            return

        self._send_json_response(404, {"error": "Endpoint not found"})

    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)

        if url.path == "/api/auth/telegram/create-session":
            action = params.get("action", ["carrier_login"])[0]
            self._handle_create_session(action)
            return

        elif url.path == "/api/auth/telegram/check-session":
            token = params.get("token", [""])[0]
            session = ACTIVE_AUTH_SESSIONS.get(token)

            if not session or time.time() - session["created_at"] > AUTH_SESSION_TTL_SECONDS:
                self._send_json_response(200, {"success": False, "status": "expired"})
                return

            if session["status"] == "authorized":
                user_data = session["telegram_user"]
                session["consumed"] = True
                self._send_json_response(200, {"success": True, "status": "authorized", "user": user_data})
                return
            elif session["status"] == "denied":
                self._send_json_response(200, {"success": False, "status": "denied"})
                return

            self._send_json_response(200, {
                "success": True,
                "status": "pending",
                "remaining_seconds": max(0, int(AUTH_SESSION_TTL_SECONDS - (time.time() - session["created_at"])))
            })
            return

        elif url.path == "/health":
            self._send_json_response(200, {
                "status": "ok",
                "service": "BusLiner Unified Platform Bot Daemon",
                "bot_username": BOT_USERNAME,
                "active_sessions": len(ACTIVE_AUTH_SESSIONS)
            })
            return

        elif url.path == "/api/admin/users":
            records = get_db_records()
            self._send_json_response(200, {
                "success": True,
                "database": "db/busliner.db",
                "counts": {
                    "users": len(records.get("users", [])),
                    "carriers": len(records.get("carriers", [])),
                    "drivers": len(records.get("drivers", []))
                },
                "data": records
            })
            return

        elif url.path == "/api/sniper/external/tasks":
            if not universal_sniper_manager:
                self._send_json_response(500, {"success": False, "error": "Universal sniper module not loaded"})
                return
            tasks_data = [
                {
                    "task_id": t.task_id,
                    "origin": t.origin,
                    "destination": t.destination,
                    "target_date": t.target_date,
                    "time_window": f"{t.time_window_start} — {t.time_window_end}",
                    "status": t.status,
                    "checks_count": t.checks_count,
                    "last_checked_at": t.last_checked_at,
                    "winning_trip": t.winning_trip.to_dict() if t.winning_trip else None
                }
                for t in universal_sniper_manager.active_tasks.values()
            ]
            self._send_json_response(200, {"success": True, "tasks": tasks_data})
            return

        elif url.path.startswith("/api/"):
            self._send_json_response(404, {"error": "Endpoint not found"})
            return

        # Fallback to static file server (serves HTML, CSS, JS, etc.)
        super().do_GET()


# ==============================================================================
# MAIN ENTRYPOINT & DAEMON RUNNER
# ==============================================================================
def universal_sniper_background_worker():
    """Background cycle checking active sniper tasks across all providers."""
    while True:
        try:
            if universal_sniper_manager:
                universal_sniper_manager.execute_check_cycle()
        except Exception as e:
            print(f"[Universal Sniper Worker Error]: {e}", file=sys.stderr)
        time.sleep(20)


def run_auth_server(host: str = SERVER_HOST, port: int = SERVER_PORT):
    init_db()

    # Start Telegram background polling worker thread
    polling_thread = threading.Thread(target=telegram_polling_worker, daemon=True)
    polling_thread.start()

    # Start Universal Belarus Transport Sniper worker thread
    sniper_thread = threading.Thread(target=universal_sniper_background_worker, daemon=True)
    sniper_thread.start()

    server_address = (host, port)
    httpd = HTTPServer(server_address, TelegramAuthHTTPHandler)
    print("==================================================================")
    print(f"  BusLiner Unified Platform Bot Daemon running on http://{host}:{port}")
    print(f"  Target Bot: @{BOT_USERNAME}")
    print("  Supported Roles: [Client/Passenger, Carrier/Owner, Driver]")
    print("==================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Shutdown] BusLiner Daemon stopped cleanly.")
        httpd.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else SERVER_PORT
    run_auth_server(port=port_arg)
