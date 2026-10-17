-- =============================================================================
-- BusLiner Partners Platform — Demonstration Seed Data
-- =============================================================================

-- 1. СТАНЦИИ И АВТОВОКЗАЛЫ
INSERT INTO stations (id, city, name, address, latitude, longitude) VALUES
('11111111-1111-1111-1111-111111111101', 'Гомель', 'Центральный автовокзал, пл. 3', 'г. Гомель, ул. Курчатова, 1', 52.4339, 30.9958),
('11111111-1111-1111-1111-111111111102', 'Минск', 'Центральный автовокзал', 'г. Минск, ул. Бобруйская, 6', 53.8906, 27.5507),
('11111111-1111-1111-1111-111111111103', 'Брест', 'Автовокзал Брест', 'г. Брест, ул. Орджоникидзе, 12', 52.0975, 23.6877),
('11111111-1111-1111-1111-111111111104', 'Гродно', 'Автовокзал Гродно', 'г. Гродно, ул. Красноармейская, 7', 53.6778, 23.8436)
ON CONFLICT (id) DO NOTHING;

-- 2. АВТОПАРКИ (CARRIERS)
INSERT INTO carriers (id, legal_name, brand_name, tax_id, iban, bank_name, bic, contact_phone, contact_email, legal_address, commission_rate, status) VALUES
('22222222-2222-2222-2222-222222222201', 'ОДО «Бурлаки-Авто»', 'Бурлаки Экспресс', '490123456', 'BY20AKBB30120000123450000000', 'ОАО «АСБ Беларусбанк»', 'AKBBBY2X', '+375 (29) 774-12-00', 'fleet@burlaki.by', 'г. Гомель, ул. Советская, 45-2', 0.0650, 'active'),
('22222222-2222-2222-2222-222222222202', 'ЧУП «АвтоСпутник-Транс»', 'АвтоСпутник', '490987654', 'BY45BPSB30121111222230000000', 'ОАО «Сбер Банк»', 'BPSBBY2X', '+375 (44) 555-88-12', 'info@autosputnik.by', 'г. Гомель, ул. Барыкина, 112', 0.0650, 'active'),
('22222222-2222-2222-2222-222222222203', 'ООО «ЗападТрансАвто»', 'Запад Экспресс', '290456789', 'BY88PJCB30123333444450000000', 'ОАО «Приорбанк»', 'PJCBBY2X', '+375 (33) 612-40-99', 'dispatch@zapadtrans.by', 'г. Брест, ул. Московская, 208', 0.0650, 'active')
ON CONFLICT (id) DO NOTHING;

-- 3. СОТРУДНИКИ И ДИСПЕТЧЕРЫ
INSERT INTO carrier_users (id, carrier_id, role, full_name, email, phone, password_hash, email_verified) VALUES
('33333333-3333-3333-3333-333333333301', '22222222-2222-2222-2222-222222222201', 'owner', 'Мельников Сергей Викторович', 'melnikov@burlaki.by', '+375 (29) 774-12-00', crypt('Password@2026', gen_salt('bf')), TRUE),
('33333333-3333-3333-3333-333333333302', '22222222-2222-2222-2222-222222222201', 'dispatcher', 'Ковалева Елена', 'dispatcher@burlaki.by', '+375 (29) 774-12-01', crypt('Dispatcher@2026', gen_salt('bf')), TRUE),
('33333333-3333-3333-3333-333333333303', NULL, 'owner', 'Ковалев Виталий Николаевич', 'vitaly.kovalev@gmail.com', '+375 (33) 998-11-22', NULL, TRUE)
ON CONFLICT (id) DO NOTHING;

-- Привязка Google OAuth
INSERT INTO carrier_user_identities (user_id, provider, provider_user_id, provider_email, raw_profile) VALUES
('33333333-3333-3333-3333-333333333303', 'google', 'google-oauth2|109845729104859123847', 'vitaly.kovalev@gmail.com', '{"name": "Виталий Ковалев", "picture": "https://lh3.googleusercontent.com/a/default-user"}'::jsonb)
ON CONFLICT (provider, provider_user_id) DO NOTHING;

-- Пример активного черновика регистрации нового автопарка
INSERT INTO carrier_onboarding_drafts (user_id, current_step, draft_data, is_completed) VALUES
('33333333-3333-3333-3333-333333333303', 3, '{"company_name": "ИП Ковалев В.Н.", "tax_id": "291884512", "iban": "BY55BAPB30120000999900000000", "bic": "BAPBBY2X", "vehicle_gov_num": "44-18 AB-1", "vehicle_model": "Mercedes Sprinter 2021", "route": "Брест — Минск"}'::jsonb, FALSE)
ON CONFLICT (id) DO NOTHING;

-- 4. ТРАНСПОРТ (МИКРОАВТОБУСЫ)
INSERT INTO vehicles (id, carrier_id, gov_number, vin, make_model, year_built, passenger_capacity, cargo_capacity_kg, bike_slots_max, amenities) VALUES
('44444444-4444-4444-4444-444444444401', '22222222-2222-2222-2222-222222222201', '77-12 AX-3', 'WV1ZZZ2EZN6011111', 'Volkswagen Crafter 50 (Свежий, 2023)', 2023, 18, 350.00, 2, '{"wifi": true, "sockets_220v": true, "ac": true, "climate": true, "usb_ports": true}'::jsonb),
('44444444-4444-4444-4444-444444444402', '22222222-2222-2222-2222-222222222202', '02-45 ВЕ-3', 'WDB9066571S222222', 'Mercedes-Benz Sprinter 519 CDI', 2022, 18, 300.00, 2, '{"wifi": true, "sockets_220v": true, "ac": true, "tv_multimedia": true}'::jsonb),
('44444444-4444-4444-4444-444444444403', '22222222-2222-2222-2222-222222222203', '89-11 MI-7', 'WDB9066571S333333', 'Mercedes-Benz Sprinter 2022', 2022, 18, 300.00, 3, '{"wifi": true, "sockets_220v": true, "ac": true, "climate": true}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- 5. ВОДИТЕЛИ
INSERT INTO drivers (id, carrier_id, full_name, phone, license_number, app_pin_hash) VALUES
('55555555-5555-5555-5555-555555555501', '22222222-2222-2222-2222-222222222201', 'Алексеев Владимир Иванович', '+375 (29) 112-33-44', '3AB 128945', crypt('1234', gen_salt('bf'))),
('55555555-5555-5555-5555-555555555502', '22222222-2222-2222-2222-222222222202', 'Сидоров Петр Васильевич', '+375 (44) 777-66-55', '3AB 984512', crypt('4321', gen_salt('bf')))
ON CONFLICT (id) DO NOTHING;

-- 6. МАРШРУТЫ
INSERT INTO routes (id, carrier_id, origin_city, destination_city, distance_km, estimated_duration_min) VALUES
('66666666-6666-6666-6666-666666666601', '22222222-2222-2222-2222-222222222201', 'Гомель', 'Минск', 312.00, 210),
('66666666-6666-6666-6666-666666666602', '22222222-2222-2222-2222-222222222202', 'Гомель', 'Минск', 312.00, 205),
('66666666-6666-6666-6666-666666666603', '22222222-2222-2222-2222-222222222203', 'Брест', 'Минск', 350.00, 240)
ON CONFLICT (id) DO NOTHING;

-- 7. ПРИМЕР РЕЙСА (ГОМЕЛЬ — МИНСК 17:00)
INSERT INTO trips (id, carrier_id, route_id, vehicle_id, driver_id, departure_at, arrival_at, base_price, sniper_enabled, status) VALUES
('77777777-7777-7777-7777-777777777701', '22222222-2222-2222-2222-222222222201', '66666666-6666-6666-6666-666666666601', '44444444-4444-4444-4444-444444444401', '55555555-5555-5555-5555-555555555501', 
 NOW() + INTERVAL '3 hours', NOW() + INTERVAL '6 hours 30 minutes', 24.00, TRUE, 'scheduled')
ON CONFLICT (id) DO NOTHING;

-- Генерация 18 мест для рейса
INSERT INTO trip_seats (trip_id, seat_number, status, sold_price, is_sniper_sale)
SELECT 
    '77777777-7777-7777-7777-777777777701',
    s,
    CASE WHEN s <= 16 THEN 'sold'::seat_status ELSE 'available'::seat_status END,
    CASE WHEN s <= 16 THEN 24.00 ELSE NULL END,
    FALSE
FROM generate_series(1, 18) AS s
ON CONFLICT (trip_id, seat_number) DO NOTHING;

-- 8. ПРИМЕР SMART CARGO ЗАКАЗОВ
INSERT INTO cargo_orders (trip_id, cargo_type, sender_name, sender_phone, recipient_phone, weight_kg, amount, tracking_code) VALUES
('77777777-7777-7777-7777-777777777701', 'bike_slot', 'Дмитрий Радченко', '+375 (29) 334-11-22', '+375 (44) 998-77-66', 14.50, 16.00, 'CRG-BIKE-881'),
('77777777-7777-7777-7777-777777777701', 'cargo_box_m', 'ООО «Автозапчасти»', '+375 (29) 667-44-33', '+375 (29) 112-22-33', 12.00, 32.00, 'CRG-BOX-904')
ON CONFLICT (tracking_code) DO NOTHING;

-- 9. ПРИМЕР ЕЖЕДНЕВНОГО КЛИРИНГА T+1 ЗА ВЧЕРАШНИЕ СУТКИ
INSERT INTO clearing_batches (carrier_id, batch_date, gross_amount, platform_fee_total, net_payout, tickets_count, cargo_count, status, payment_order_num, paid_at) VALUES
('22222222-2222-2222-2222-222222222201', CURRENT_DATE - 1, 8460.00, 549.90, 7910.10, 342, 14, 'transferred', 'PAY-BY-2026-04192', NOW() - INTERVAL '4 hours')
ON CONFLICT (carrier_id, batch_date) DO NOTHING;
