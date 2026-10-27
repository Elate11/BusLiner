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
