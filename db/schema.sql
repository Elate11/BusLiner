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
    'manager',              -- Управляющий автопарком (управление рейсами и заменами)
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

CREATE TYPE auth_provider_type AS ENUM (
    'google',               -- Google OAuth 2.0 / Workspace
    'telegram',             -- Telegram Login Widget
    'email_password',       -- Классический вход по email и паролю
    'phone_otp'             -- Вход по номеру телефона и SMS-коду
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
    carrier_id UUID REFERENCES carriers(id) ON DELETE CASCADE, -- NULL на этапе онбординга
    role user_role NOT NULL DEFAULT 'owner',
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(30) UNIQUE,
    password_hash VARCHAR(255),                                -- NULL при входе через Google/Telegram
    avatar_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_carrier_users_carrier ON carrier_users(carrier_id);
CREATE INDEX idx_carrier_users_email ON carrier_users(email);
CREATE INDEX idx_carrier_users_phone ON carrier_users(phone);

-- ПРИВЯЗКА СОЦИАЛЬНЫХ ПРОВАЙДЕРОВ ВХОДА (GOOGLE, TELEGRAM И ДР.)
CREATE TABLE carrier_user_identities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES carrier_users(id) ON DELETE CASCADE,
    provider auth_provider_type NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,                    -- Google sub ID / Telegram ID
    provider_email VARCHAR(100),
    raw_profile JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX idx_user_identities_user ON carrier_user_identities(user_id);

-- ЧЕРНОВИКИ И ШАГИ ОНБОРДИНГА АВТОПАРКА (MULTI-STEP WIZARD)
CREATE TABLE carrier_onboarding_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES carrier_users(id) ON DELETE CASCADE,
    current_step SMALLINT NOT NULL DEFAULT 1,                  -- 1: Профиль, 2: Юрлицо, 3: Флот, 4: Маршрут, 5: Завершено
    draft_data JSONB NOT NULL DEFAULT '{}'::jsonb,             -- Сохраненные поля каждого шага
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_onboarding_drafts_user ON carrier_onboarding_drafts(user_id);

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
-- =============================================================================
-- BusLiner Production Migration 002: Seat Sniper 2.0 & Offline Manifest Infrastructure
-- Architecture: Hardened PostgreSQL Schema with Strict Invariants and Zero-Oversell
-- Target: PostgreSQL 14+
-- =============================================================================

-- Ensure required crypto extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. HARDEN EXISTING TABLE INVARIANTS: trip_seats
-- =============================================================================

-- Ensure strict invariant: One seat per trip once at DB level
-- The unique constraint UNIQUE(trip_id, seat_number) guarantees that no duplicate seat record
-- can ever be inserted for any given trip.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_trip_seats_trip_seat_no'
    ) THEN
        ALTER TABLE trip_seats 
        ADD CONSTRAINT uq_trip_seats_trip_seat_no UNIQUE (trip_id, seat_number);
    END IF;
END $$;

-- Partial unique index: At most ONE active sold/held status per physical seat
CREATE UNIQUE INDEX IF NOT EXISTS idx_trip_seats_single_reservation
    ON trip_seats (trip_id, seat_number)
    WHERE status IN ('held', 'sold');

-- =============================================================================
-- 2. ENUMS FOR SEAT SNIPER ENGINE
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sniper_order_status') THEN
        CREATE TYPE sniper_order_status AS ENUM (
            'active',           -- Активен, слушает события освобождения мест в реальном времени
            'matched',          -- Найдено подходящее место, начат транзакционный захват
            'reserved',         -- Место успешно зарезервировано, hold установлен
            'completed',        -- Билет фискализирован и оплачен
            'cancelled',        -- Отозван пользователем вручную
            'expired',          -- Окно вылета истекло (рейс отправился)
            'failed_beaten'     -- Место перехвачено более ранней заявкой в очереди
        );
    END IF;
END $$;

-- =============================================================================
-- 3. SEAT SNIPER ORDERS (ОРДЕРА НА АВТОВЫКУП КРЕСЕЛ)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sniper_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,                              -- Внешний ID пассажира (carrier_users или web-клиент)
    client_identity VARCHAR(100) NOT NULL,              -- Телефон или Telegram ID заказчика
    route_id UUID NOT NULL REFERENCES routes(id) ON DELETE RESTRICT,
    departure_date DATE NOT NULL,
    time_window_start TIME NOT NULL,
    time_window_end TIME NOT NULL,
    preferred_seat_type VARCHAR(20) NOT NULL DEFAULT 'any', -- 'any', 'window', 'aisle', 'front_vip'
    passenger_full_name VARCHAR(150) NOT NULL,
    passenger_phone VARCHAR(30) NOT NULL,
    passenger_passport_hash VARCHAR(64) NOT NULL,       -- Хэш паспорта: антискальпинг, запрет перепродажи
    auto_debit_consent BOOLEAN NOT NULL DEFAULT TRUE,   -- Защита от спама: явный акцепт автосписания
    max_price_byn NUMERIC(8,2) NOT NULL,                -- Предельный бюджет автовыкупа
    status sniper_order_status NOT NULL DEFAULT 'active',
    queue_priority BIGINT NOT NULL DEFAULT 0,          -- Приоритет в очереди (FIFO по created_at)
    cancelled_at TIMESTAMPTZ,
    cancellation_reason VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_sniper_auto_debit CHECK (auto_debit_consent = TRUE),
    CONSTRAINT chk_sniper_time_window CHECK (time_window_end >= time_window_start),
    CONSTRAINT chk_sniper_positive_price CHECK (max_price_byn > 0)
);

CREATE INDEX IF NOT EXISTS idx_sniper_orders_lookup 
    ON sniper_orders(route_id, departure_date, status)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_sniper_orders_user 
    ON sniper_orders(user_id, status);

CREATE INDEX IF NOT EXISTS idx_sniper_orders_queue
    ON sniper_orders(route_id, departure_date, queue_priority ASC)
    WHERE status = 'active';

-- Anti-Abuse Constraint: Partial unique index to limit active snipers per passenger
-- A passenger cannot have more than 3 active snipers on the exact same route and date
CREATE INDEX IF NOT EXISTS idx_sniper_anti_spam_route_date
    ON sniper_orders(client_identity, route_id, departure_date)
    WHERE status = 'active';

-- =============================================================================
-- 4. REAL-TIME SEAT RELEASE EVENTS (ИСТОЧНИК СОБЫТИЙ ДЛЯ PUB/SUB)
-- =============================================================================

CREATE TABLE IF NOT EXISTS seat_release_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    seat_id UUID NOT NULL REFERENCES trip_seats(id) ON DELETE CASCADE,
    seat_number SMALLINT NOT NULL,
    release_reason VARCHAR(50) NOT NULL,                -- 'passenger_refund', 'hold_ttl_expiry', 'carrier_release'
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,       -- Предотвращает дублирующую обработку одного события
    released_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    matched_order_id UUID REFERENCES sniper_orders(id),
    latency_ms NUMERIC(8,2),                            -- Измеримая метрика release -> reserve
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_seat_release_unprocessed 
    ON seat_release_events(trip_id, processed_at)
    WHERE processed_at IS NULL;

-- =============================================================================
-- 5. SEAT SNIPER EXECUTIONS & AUDIT LOG (РЕЗУЛЬТАТЫ СРАБАТЫВАНИЯ)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sniper_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES sniper_orders(id) ON DELETE RESTRICT,
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE RESTRICT,
    seat_id UUID NOT NULL REFERENCES trip_seats(id) ON DELETE RESTRICT,
    event_id UUID NOT NULL REFERENCES seat_release_events(id) ON DELETE RESTRICT,
    release_timestamp TIMESTAMPTZ NOT NULL,
    lock_acquired_timestamp TIMESTAMPTZ NOT NULL,
    reserve_timestamp TIMESTAMPTZ NOT NULL,
    latency_ms NUMERIC(8,2) NOT NULL,                   -- Итоговая метрика release -> reserve в миллисекундах
    amount_paid NUMERIC(8,2) NOT NULL,
    miles_debited INTEGER NOT NULL DEFAULT 0,
    ticket_id UUID REFERENCES tickets(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_sniper_execution_seat UNIQUE (trip_id, seat_id)
);

CREATE INDEX IF NOT EXISTS idx_sniper_exec_order ON sniper_executions(order_id);
CREATE INDEX IF NOT EXISTS idx_sniper_exec_latency ON sniper_executions(latency_ms);

-- =============================================================================
-- 6. GLOBAL IDEMPOTENCY KEYS (ПРЕДОТВРАЩЕНИЕ ДВОЙНЫХ СПИСАНИЙ И ОВЕРБУКИНГА)
-- =============================================================================

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key VARCHAR(128) PRIMARY KEY,
    scope VARCHAR(50) NOT NULL,                         -- 'sniper_reserve', 'ticket_payment', 'miles_debit'
    status VARCHAR(20) NOT NULL DEFAULT 'processing',   -- 'processing', 'completed', 'failed'
    response_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idempotency_expiry ON idempotency_keys(expires_at);

-- =============================================================================
-- 7. TELEGRAM NOTIFICATION OUTBOX WITH STRICT IDEMPOTENCY
-- =============================================================================

CREATE TABLE IF NOT EXISTS notification_outbox (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,                      -- Telegram Chat ID или User UUID
    trip_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,                    -- 'sniper_intercepted', 'ticket_ready', 'boarding_gate', 'refund_issued'
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',       -- 'pending', 'sent', 'failed'
    retry_count SMALLINT NOT NULL DEFAULT 0,
    max_retries SMALLINT NOT NULL DEFAULT 5,
    last_error TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Инвариант: пользователь не получает повторных уведомлений одного типа по одному рейсу
    CONSTRAINT uq_notification_user_trip_event UNIQUE (user_id, trip_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_notification_outbox_pending 
    ON notification_outbox(status, created_at)
    WHERE status = 'pending';

-- =============================================================================
-- 8. DRIVER OFFLINE CHECK-IN INFRASTRUCTURE (КРИПТОПОДПИСЬ И СИНХРОНИЗАЦИЯ)
-- =============================================================================

-- Версионирование манифеста для офлайн-кэширования
CREATE TABLE IF NOT EXISTS manifest_cache_versions (
    trip_id UUID PRIMARY KEY REFERENCES trips(id) ON DELETE CASCADE,
    version BIGINT NOT NULL DEFAULT 1,
    manifest_signature VARCHAR(128) NOT NULL,           -- HMAC-SHA256 хеш актуального состава пассажиров
    passenger_count SMALLINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Журнал синхронизации офлайн-посадки водителя
CREATE TABLE IF NOT EXISTS offline_sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE RESTRICT,
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE RESTRICT,
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE RESTRICT,
    client_action_time TIMESTAMPTZ NOT NULL,            -- Локальное время водителя на перроне
    server_synced_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    qr_signature VARCHAR(128) NOT NULL,                 -- Криптографическая подпись проверенного билета
    is_valid_signature BOOLEAN NOT NULL DEFAULT TRUE,
    sync_conflict BOOLEAN NOT NULL DEFAULT FALSE,       -- Флаг коллизии (напр. пассажир уже посажен другим терминалом)
    conflict_resolution VARCHAR(100),
    device_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_offline_sync_trip_ticket UNIQUE (trip_id, ticket_id)
);

CREATE INDEX IF NOT EXISTS idx_offline_sync_trip ON offline_sync_logs(trip_id);
CREATE INDEX IF NOT EXISTS idx_offline_sync_conflicts ON offline_sync_logs(sync_conflict) WHERE sync_conflict = TRUE;

-- =============================================================================
-- 9. AUDIT TRIGGER FOR UPDATED_AT
-- =============================================================================

CREATE OR REPLACE TRIGGER trg_sniper_orders_updated_at
    BEFORE UPDATE ON sniper_orders
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();

CREATE OR REPLACE TRIGGER trg_notification_outbox_updated_at
    BEFORE UPDATE ON notification_outbox
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
