-- =============================================================================
-- BusLiner Partners Platform — PostgreSQL Database Schema
-- Architecture: Relational Domain Model for Intercity Fleet Management
-- Target: PostgreSQL 14+
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Helper trigger function to maintain updated_at timestamps
CREATE OR REPLACE FUNCTION set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 1. ENUMS (DOMAIN VALUE TYPES)
-- =============================================================================

CREATE TYPE carrier_status AS ENUM (
    'pending_verification', -- Регистрация подана, на проверке документов
    'active',               -- Автопарк активен, рейсы в расписании
    'suspended',            -- Временно заблокирован (задолженность, проверка)
    'archived'              -- Договор расторгнут
);

CREATE TYPE user_role AS ENUM (
    'owner',                -- Руководитель автопарка (полный доступ, фин. отчеты)
    'dispatcher',           -- Главный диспетчер (управление рейсами и заменами)
    'accountant',           -- Бухгалтер (счета, акты, реестры T+1)
    'driver'                -- Водитель (мобильное приложение для QR-посадки)
);

CREATE TYPE trip_status AS ENUM (
    'scheduled',            -- Запланирован в расписании, открыта продажа
    'boarding',             -- Идет посадка пассажиров по QR-кодам
    'in_transit',           -- Микроавтобус на трассе в пути
    'completed',            -- Рейс благополучно завершен, фискализирован
    'cancelled'             -- Отменен (с 100% автовозвратом средств)
);

CREATE TYPE seat_status AS ENUM (
    'available',            -- Свободно для покупки
    'held',                 -- Временный hold на 10 минут при чекауте
    'sold',                 -- Успешно оплачено и выкуплено
    'blocked'               -- Технически заблокировано перевозчиком (багаж/служебное)
);

CREATE TYPE cargo_type AS ENUM (
    'bike_slot',            -- Слот под велосипед на заднем креплении (+8-16 BYN)
    'cargo_box_s',          -- Стандартная посылка до 5 кг (+10 BYN)
    'cargo_box_m',          -- Средняя коробка до 15 кг (+18 BYN)
    'cargo_box_l'           -- Негабаритный груз Cargo до 30 кг (+32 BYN)
);

CREATE TYPE clearing_status AS ENUM (
    'calculated',           -- Сведен в полночь, ожидает выгрузки в банк
    'processing',           -- Платежное поручение отправлено в банк
    'transferred',          -- Средства успешно зачислены на р/с перевозчика (T+1)
    'reconciled'            -- Закрыт актом сверки и подписан ЭЦП
);

-- =============================================================================
-- 2. АВТОПАРКИ И ЮРИДИЧЕСКИЕ ЛИЦА (CARRIERS)
-- =============================================================================

CREATE TABLE carriers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_name VARCHAR(255) NOT NULL,              -- Напр. ОДО «Бурлаки-Авто» / ИП Ковалев В.Н.
    brand_name VARCHAR(100) NOT NULL,              -- Напр. «Бурлаки Экспресс»
    tax_id VARCHAR(30) UNIQUE NOT NULL,            -- УНП (Беларусь) / ИНН (РФ)
    iban VARCHAR(34) NOT NULL,                     -- Расчетный счет IBAN (напр. BY20AKBB...)
    bank_name VARCHAR(200) NOT NULL,               -- Название банка
    bic VARCHAR(15) NOT NULL,                      -- БИК банка
    contact_phone VARCHAR(30) NOT NULL,
    contact_email VARCHAR(100) NOT NULL,
    legal_address TEXT NOT NULL,
    commission_rate NUMERIC(5,4) NOT NULL DEFAULT 0.0650, -- Базовая комиссия 6.5%
    status carrier_status NOT NULL DEFAULT 'pending_verification',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_carriers_status ON carriers(status);
CREATE INDEX idx_carriers_tax_id ON carriers(tax_id);

CREATE TRIGGER trg_carriers_updated_at
    BEFORE UPDATE ON carriers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();

-- =============================================================================
-- 3. СОТРУДНИКИ И ДОСТУПЫ (CARRIER USERS & RBAC)
-- =============================================================================

CREATE TABLE carrier_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    carrier_id UUID NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'dispatcher',
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(30) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_carrier_users_carrier ON carrier_users(carrier_id);
CREATE INDEX idx_carrier_users_email ON carrier_users(email);

-- =============================================================================
-- 4. АВТОПАРК (VEHICLES / FLEET)
-- =============================================================================

CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    carrier_id UUID NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    gov_number VARCHAR(20) NOT NULL UNIQUE,        -- Напр. 77-12 AX-3
    vin VARCHAR(17) UNIQUE,
    make_model VARCHAR(100) NOT NULL,              -- Mercedes-Benz Sprinter 519 CDI / VW Crafter
    year_built SMALLINT NOT NULL,
    passenger_capacity SMALLINT NOT NULL DEFAULT 18,
    cargo_capacity_kg NUMERIC(6,2) DEFAULT 300.00,
    bike_slots_max SMALLINT DEFAULT 2,
    amenities JSONB DEFAULT '{"wifi": true, "sockets_220v": true, "ac": true, "climate": true}'::jsonb,
    tech_inspection_valid_until DATE,
    insurance_valid_until DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vehicles_carrier ON vehicles(carrier_id);
CREATE INDEX idx_vehicles_gov_number ON vehicles(gov_number);

-- =============================================================================
-- 5. ВОДИТЕЛИ (DRIVERS)
-- =============================================================================

CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    carrier_id UUID NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) UNIQUE NOT NULL,
    license_number VARCHAR(50) NOT NULL,
    categories VARCHAR(20) DEFAULT 'B,D',
    app_pin_hash VARCHAR(255) NOT NULL,            -- Пин-код для входа в приложение сканера
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drivers_carrier ON drivers(carrier_id);
CREATE INDEX idx_drivers_phone ON drivers(phone);

-- =============================================================================
-- 6. МАРШРУТНАЯ СЕТЬ И ОСТАНОВКИ (ROUTES & STOPS)
-- =============================================================================

CREATE TABLE stations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city VARCHAR(100) NOT NULL,                    -- Минск, Гомель, Брест, Гродно
    name VARCHAR(150) NOT NULL,                    -- «Центральный автовокзал, пл. 3»
    address TEXT,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    carrier_id UUID NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    origin_city VARCHAR(100) NOT NULL,
    destination_city VARCHAR(100) NOT NULL,
    distance_km NUMERIC(6,2) NOT NULL,
    estimated_duration_min INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE route_stops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    station_id UUID NOT NULL REFERENCES stations(id),
    stop_order SMALLINT NOT NULL,                  -- 1 = отправление, 2..N = промежуточные
    arrival_offset_min INTEGER NOT NULL DEFAULT 0, -- Смещение прибытия в минутах от старта
    departure_offset_min INTEGER NOT NULL DEFAULT 0,
    UNIQUE(route_id, stop_order)
);

-- =============================================================================
-- 7. РЕЙСЫ И РАСПИСАНИЕ (TRIPS)
-- =============================================================================

CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    carrier_id UUID NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    route_id UUID NOT NULL REFERENCES routes(id),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    driver_id UUID REFERENCES drivers(id),
    departure_at TIMESTAMPTZ NOT NULL,
    arrival_at TIMESTAMPTZ NOT NULL,
    base_price NUMERIC(8,2) NOT NULL,              -- Напр. 24.00 BYN
    sniper_enabled BOOLEAN NOT NULL DEFAULT TRUE,  -- Алгоритм динамической допродажи Снайпер 2.0
    status trip_status NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trips_departure ON trips(departure_at);
CREATE INDEX idx_trips_carrier_status ON trips(carrier_id, status);
CREATE INDEX idx_trips_route_date ON trips(route_id, departure_at);

-- =============================================================================
-- 8. МЕСТА НА РЕЙСЕ (TRIP SEATS & OPTIMISTIC CONCURRENCY)
-- =============================================================================

CREATE TABLE trip_seats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    seat_number SMALLINT NOT NULL,
    status seat_status NOT NULL DEFAULT 'available',
    sold_price NUMERIC(8,2),
    is_sniper_sale BOOLEAN NOT NULL DEFAULT FALSE, -- Закрыто ли через алгоритм Снайпер 2.0
    held_until TIMESTAMPTZ,                        -- Бронь на время оплаты (10 мин)
    version INTEGER NOT NULL DEFAULT 1,            -- Оптимистическая блокировка против овербукинга
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(trip_id, seat_number)
);

CREATE INDEX idx_trip_seats_status ON trip_seats(trip_id, status);

-- =============================================================================
-- 9. БИЛЕТЫ И ОПЛАТА (TICKETS & QR VERIFICATION)
-- =============================================================================

CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_seat_id UUID NOT NULL REFERENCES trip_seats(id),
    ticket_number VARCHAR(30) UNIQUE NOT NULL,     -- Публичный номер билета (BL-2026-89412)
    passenger_name VARCHAR(150) NOT NULL,
    passenger_phone VARCHAR(30) NOT NULL,
    qr_token UUID UNIQUE DEFAULT uuid_generate_v4(), -- Неподделываемый токен для сканера водителя
    amount_paid NUMERIC(8,2) NOT NULL,
    platform_fee NUMERIC(8,2) NOT NULL,            -- Удержанная комиссия платформы (6.5%)
    carrier_amount NUMERIC(8,2) NOT NULL,          -- Чистая выручка перевозчика (93.5%)
    fiscal_receipt_id VARCHAR(100),                -- Регистрация чека СКНО (СТБ 1389-2003)
    is_boarded BOOLEAN NOT NULL DEFAULT FALSE,     -- Факт посадки в салон
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tickets_qr_token ON tickets(qr_token);
CREATE INDEX idx_tickets_phone ON tickets(passenger_phone);

-- =============================================================================
-- 10. SMART CARGO (БАГАЖ И ЭКСПРЕСС-ОТПРАВЛЕНИЯ)
-- =============================================================================

CREATE TABLE cargo_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id),
    cargo_type cargo_type NOT NULL,
    sender_name VARCHAR(150) NOT NULL,
    sender_phone VARCHAR(30) NOT NULL,
    recipient_phone VARCHAR(30) NOT NULL,
    weight_kg NUMERIC(5,2),
    amount NUMERIC(8,2) NOT NULL,
    tracking_code VARCHAR(20) UNIQUE NOT NULL,     -- CRG-7842
    qr_token UUID UNIQUE DEFAULT uuid_generate_v4(),
    is_loaded BOOLEAN NOT NULL DEFAULT FALSE,
    is_delivered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cargo_trip ON cargo_orders(trip_id);
CREATE INDEX idx_cargo_tracking ON cargo_orders(tracking_code);

-- =============================================================================
-- 11. ЛОГИ ПОСАДКИ И ТЕЛЕМЕТРИЯ (BOARDING LOGS)
-- =============================================================================

CREATE TABLE boarding_logs (
    id BIGSERIAL PRIMARY KEY,
    ticket_id UUID NOT NULL REFERENCES tickets(id),
    driver_id UUID NOT NULL REFERENCES drivers(id),
    scanned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    gps_lat NUMERIC(9,6),
    gps_lon NUMERIC(9,6),
    device_info VARCHAR(150)
);

CREATE INDEX idx_boarding_logs_ticket ON boarding_logs(ticket_id);
CREATE INDEX idx_boarding_logs_scanned_at ON boarding_logs(scanned_at);

-- =============================================================================
-- 12. ЕЖЕДНЕВНЫЙ КЛИРИНГ T+1 (CLEARING BATCHES & RECONCILIATION)
-- =============================================================================

CREATE TABLE clearing_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    carrier_id UUID NOT NULL REFERENCES carriers(id),
    batch_date DATE NOT NULL,                      -- Дата завершенных рейсов
    gross_amount NUMERIC(10,2) NOT NULL,           -- Общий объем выручки по билетам и карго
    platform_fee_total NUMERIC(10,2) NOT NULL,     -- Комиссия платформы
    net_payout NUMERIC(10,2) NOT NULL,             -- Чистая сумма к зачислению на р/с перевозчика
    tickets_count INTEGER NOT NULL,
    cargo_count INTEGER NOT NULL,
    status clearing_status NOT NULL DEFAULT 'calculated',
    payment_order_num VARCHAR(50),                 -- Номер платежного поручения банка
    paid_at TIMESTAMPTZ,                           -- Точное время проведения банком
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(carrier_id, batch_date)
);

CREATE INDEX idx_clearing_batches_carrier ON clearing_batches(carrier_id, batch_date);
CREATE INDEX idx_clearing_batches_status ON clearing_batches(status);
