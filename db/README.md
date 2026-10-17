# База данных BusLiner Partners (PostgreSQL)

Реляционная архитектура базы данных для B2B-платформы автоперевозчиков **BusLiner Partners** (монетизация, автоматизация управления флотом, алгоритм Снайпер 2.0, Smart Cargo и клиринг T+1).

---

## 1. Быстрый старт

### Требования
* PostgreSQL 14+
* Установленные расширения `uuid-ossp`, `pgcrypto`

### Развёртывание схемы и демо-данных
```bash
# 1. Создание базы данных
createdb busliner_db

# 2. Применение схемы
psql -d busliner_db -f db/schema.sql

# 3. Загрузка демонстрационных данных (флоты, рейсы, места, клиринг)
psql -d busliner_db -f db/seeds.sql
```

Или через одну команду в Docker:
```bash
docker run --name busliner-pg -e POSTGRES_DB=busliner_db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16-alpine
psql -h localhost -U postgres -d busliner_db -f db/schema.sql
psql -h localhost -U postgres -d busliner_db -f db/seeds.sql
```

---

## 2. Структура таблиц и назначение

| Таблица | Назначение | Ключевые особенности |
| :--- | :--- | :--- |
| **`carriers`** | Юрлица автопарков и реквизиты | УНП, IBAN, БИК, комиссия (6.5%), статус верификации |
| **`carrier_users`** | Доступы в ЛК партнёра | Роли: `owner`, `manager`, `accountant`, `driver` (RBAC) |
| **`vehicles`** | Микроавтобусы флота | Госномер, VIN, вместимость (18 мест), JSONB-удобства |
| **`drivers`** | Водители | Категории ВУ, пин-код для входа в приложение сканера |
| **`stations`** | Автовокзалы и платформы | Город, координаты GPS (lat, lon) для посадки |
| **`routes`** | Направления (Гомель—Минск и др.) | Дистанция, расчетное время в пути |
| **`trips`** | Конкретные рейсы в расписании | Дата, борт, водитель, базовая цена, статус |
| **`trip_seats`** | Места в салоне на рейс | Статус (`available`, `held`, `sold`), колонка `version` |
| **`tickets`** | Оплаченные пассажирские билеты | Неподделываемый `qr_token`, фискальный признак СТБ 1389 |
| **`cargo_orders`** | Smart Cargo (багаж и посылки) | Вело-слоты, коробки, трек-код `CRG-XXXX` |
| **`boarding_logs`** | Телеметрия посадки | Фиксация GPS-координат и времени сканирования QR |
| **`clearing_batches`** | Ежедневный клиринг T+1 | Автоматический расчет чистой выплаты на р/с перевозчика |

---

## 3. Критические архитектурные решения

### 3.1. Защита от овербукинга (Optimistic Concurrency Control)
Каждое место в таблице `trip_seats` защищено колонкой `version` и уникальным составным ключом `UNIQUE(trip_id, seat_number)`.

При попытке забронировать место выполняется атомарный запрос:
```sql
UPDATE trip_seats
SET status = 'held',
    held_until = NOW() + INTERVAL '10 minutes',
    version = version + 1
WHERE id = $seat_id
  AND status = 'available'
  AND version = $expected_version;
```
Если запрос вернул `0 строк`, значит другое приложение уже удерживает или выкупило это место — овербукинг физически невозможен.

### 3.2. Точность финансовых расчетов
Все денежные суммы используют тип `NUMERIC(8,2)` и `NUMERIC(10,2)`. Плавающие точки (`FLOAT`/`REAL`) запрещены во избежание погрешностей копеек при клиринге T+1.

### 3.3. Безопасность проверки билетов
Поле `qr_token` в таблице `tickets` генерируется как криптографический случайный `UUIDv4`. Пассажир получает QR-код с этим токеном. Водитель при сканировании передает токен в защищенный backend API, что исключает подделку билета через угадывание номеров.

---

## 4. Примеры типовых запросов для управления автопарком и аналитики

### Сводка рейса для панели управления флотом (заполняемость и выручка):
```sql
SELECT 
    t.id AS trip_id,
    t.departure_at,
    v.gov_number,
    v.make_model,
    COUNT(ts.id) FILTER (WHERE ts.status = 'sold') AS sold_seats,
    v.passenger_capacity AS total_seats,
    ROUND((COUNT(ts.id) FILTER (WHERE ts.status = 'sold')::numeric / v.passenger_capacity) * 100, 1) AS load_pct,
    COALESCE(SUM(ts.sold_price), 0) + COALESCE((SELECT SUM(amount) FROM cargo_orders WHERE trip_id = t.id), 0) AS total_revenue_byn
FROM trips t
JOIN vehicles v ON t.vehicle_id = v.id
LEFT JOIN trip_seats ts ON ts.trip_id = t.id
WHERE t.carrier_id = '22222222-2222-2222-2222-222222222201'
  AND t.departure_at::date = CURRENT_DATE
GROUP BY t.id, t.departure_at, v.gov_number, v.make_model, v.passenger_capacity
ORDER BY t.departure_at ASC;
```

### Сведение реестра клиринга T+1 за прошедшие сутки:
```sql
SELECT 
    c.legal_name,
    c.iban,
    cb.batch_date,
    cb.gross_amount,
    cb.platform_fee_total,
    cb.net_payout,
    cb.status,
    cb.payment_order_num
FROM clearing_batches cb
JOIN carriers c ON cb.carrier_id = c.id
WHERE cb.batch_date = CURRENT_DATE - 1;
```
