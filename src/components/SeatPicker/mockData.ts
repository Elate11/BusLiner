import { VehicleLayout, SeatData } from './types';

/**
 * 1. МИКРОАВТОБУС МЕЖДУГОРОДНИЙ (19 мест, компоновка 2+1)
 * Прототип: Mercedes-Benz Sprinter 519 / Iveco Daily (BusLiner Express)
 * Структура сетки: 3 колонки кресел + проход (колонки 0: окно левое, 1: проход левый, 2: проход, 3: окно правое)
 */
export const minibus19MockLayout: VehicleLayout = {
  id: 'layout-minibus-19',
  type: 'minibus_2_1',
  name: 'Mercedes-Benz Sprinter Tourer',
  carrierName: 'BusLiner Intercity Express',
  totalSeats: 19,
  rowsCount: 7,
  columnsCount: 3, // левый борт: 2 кресла, правый борт: 1 кресло
  aisleColumnIndex: 2, // проход разделяет левую пару и правое кресло
  entrances: [
    { id: 'ent-1', side: 'right', row: 1, label: 'Посадочная дверь с электроподножкой' }
  ],
  serviceZones: [
    { id: 'zone-driver', type: 'driver', row: 1, col: 0, colSpan: 2, label: 'Кабина водителя' },
    { id: 'zone-luggage', type: 'luggage', row: 7, col: 0, colSpan: 3, label: 'Багажный отсек 1.8 м³' }
  ],
  seats: [
    // Ряд 2 (сразу за кабиной и входной дверью)
    {
      id: 'mb-1', seatNumber: '1', row: 2, col: 0, type: 'window', price: 950, extraFee: 100,
      status: 'disabled', features: ['Спецоборудование для ОВЗ', '220V / Type-C', 'Увеличенное место для ног'],
      accessibleLabel: 'Место 1, у левого окна, приоритетное для маломобильных пассажиров, 950 ₽'
    },
    {
      id: 'mb-2', seatNumber: '2', row: 2, col: 1, type: 'aisle', price: 900, extraFee: 50,
      status: 'available', features: ['220V / Type-C', 'Увеличенное место для ног'],
      accessibleLabel: 'Место 2, у прохода, увеличенное пространство для ног, 900 ₽'
    },
    // Напротив двери в ряду 2 кресла справа нет (проходная зона)

    // Ряд 3
    {
      id: 'mb-3', seatNumber: '3', row: 3, col: 0, type: 'window', price: 850, extraFee: 0,
      status: 'occupied', features: ['220V / Type-C', 'Откидной столик'],
      accessibleLabel: 'Место 3, у левого окна, 850 ₽, занято'
    },
    {
      id: 'mb-4', seatNumber: '4', row: 3, col: 1, type: 'aisle', price: 850, extraFee: 0,
      status: 'occupied', features: ['220V / Type-C', 'Откидной столик'],
      accessibleLabel: 'Место 4, у прохода, 850 ₽, занято'
    },
    {
      id: 'mb-5', seatNumber: '5', row: 3, col: 2, type: 'window', price: 950, extraFee: 100,
      status: 'available', features: ['Одиночное кресло', 'Панорамный вид', '220V / Type-C'],
      accessibleLabel: 'Место 5, одиночное кресло у правого окна, 950 ₽, доступно'
    },

    // Ряд 4
    {
      id: 'mb-6', seatNumber: '6', row: 4, col: 0, type: 'window', price: 850, extraFee: 0,
      status: 'available', features: ['220V / Type-C', 'Откидной столик'],
      accessibleLabel: 'Место 6, у левого окна, 850 ₽, доступно'
    },
    {
      id: 'mb-7', seatNumber: '7', row: 4, col: 1, type: 'aisle', price: 850, extraFee: 0,
      status: 'female-only', features: ['Женское купе/ряд', '220V / Type-C'],
      accessibleLabel: 'Место 7, у прохода, только для женщин, 850 ₽'
    },
    {
      id: 'mb-8', seatNumber: '8', row: 4, col: 2, type: 'window', price: 950, extraFee: 100,
      status: 'available', features: ['Одиночное кресло', '220V / Type-C'],
      accessibleLabel: 'Место 8, одиночное кресло у правого окна, 950 ₽, доступно'
    },

    // Ряд 5 (Колесная арка)
    {
      id: 'mb-9', seatNumber: '9', row: 5, col: 0, type: 'window', price: 800, extraFee: -50,
      status: 'available', features: ['220V / Type-C', 'Рядом колесная арка'],
      accessibleLabel: 'Место 9, у левого окна над колесной аркой, скидка 50 ₽, 800 ₽'
    },
    {
      id: 'mb-10', seatNumber: '10', row: 5, col: 1, type: 'aisle', price: 850, extraFee: 0,
      status: 'available', features: ['220V / Type-C'],
      accessibleLabel: 'Место 10, у прохода, 850 ₽, доступно'
    },
    {
      id: 'mb-11', seatNumber: '11', row: 5, col: 2, type: 'window', price: 900, extraFee: 50,
      status: 'blocked', features: ['Служебное бронирование перевозчика'],
      accessibleLabel: 'Место 11, заблокировано перевозчиком'
    },

    // Ряд 6
    {
      id: 'mb-12', seatNumber: '12', row: 6, col: 0, type: 'window', price: 850, extraFee: 0,
      status: 'available', features: ['220V / Type-C', 'Откидной столик'],
      accessibleLabel: 'Место 12, у левого окна, 850 ₽, доступно'
    },
    {
      id: 'mb-13', seatNumber: '13', row: 6, col: 1, type: 'aisle', price: 850, extraFee: 0,
      status: 'available', features: ['220V / Type-C', 'Откидной столик'],
      accessibleLabel: 'Место 13, у прохода, 850 ₽, доступно'
    },
    {
      id: 'mb-14', seatNumber: '14', row: 6, col: 2, type: 'window', price: 950, extraFee: 100,
      status: 'available', features: ['Одиночное кресло', '220V / Type-C'],
      accessibleLabel: 'Место 14, одиночное кресло у правого окна, 950 ₽, доступно'
    },

    // Ряд 7 (Задний диван из 5 мест, ограниченный наклон спинки)
    {
      id: 'mb-15', seatNumber: '15', row: 7, col: 0, type: 'limited-recline', price: 750, extraFee: -100,
      status: 'available', features: ['Не откидывается спинка', '220V / Type-C'],
      accessibleLabel: 'Место 15, задний ряд у окна, не откидывается спинка, скидка 100 ₽, 750 ₽'
    },
    {
      id: 'mb-16', seatNumber: '16', row: 7, col: 1, type: 'limited-recline', price: 750, extraFee: -100,
      status: 'available', features: ['Не откидывается спинка', '220V / Type-C'],
      accessibleLabel: 'Место 16, задний ряд, не откидывается спинка, 750 ₽'
    },
    {
      id: 'mb-17', seatNumber: '17', row: 7, col: 2, type: 'limited-recline', price: 700, extraFee: -150,
      status: 'available', features: ['Центральное место', 'Не откидывается спинка'],
      accessibleLabel: 'Место 17, задний ряд по центру, 700 ₽'
    },
    {
      id: 'mb-18', seatNumber: '18', row: 7, col: 3, type: 'limited-recline', price: 750, extraFee: -100,
      status: 'male-only', features: ['Только для мужчин', 'Не откидывается спинка'],
      accessibleLabel: 'Место 18, задний ряд, только для мужчин, 750 ₽'
    },
    {
      id: 'mb-19', seatNumber: '19', row: 7, col: 4, type: 'limited-recline', price: 750, extraFee: -100,
      status: 'available', features: ['Не откидывается спинка', '220V / Type-C'],
      accessibleLabel: 'Место 19, задний ряд у правого окна, 750 ₽'
    }
  ]
};

/**
 * 2. ТУРИСТИЧЕСКИЙ ЛАЙНЕР ДАЛЬНЕГО СЛЕДОВАНИЯ (49 мест, компоновка 2+2)
 * Прототип: Scania Touring / MAN Lion's Coach / Setra S 516 (FlixBus / Ecolines)
 * Оснащение: Туалет (WC) в середине, средняя дверь, кофе-зона, панорамные места спереди
 */
export const coach49MockLayout: VehicleLayout = {
  id: 'layout-coach-49',
  type: 'coach_2_2',
  name: 'Scania Touring HD 12M',
  carrierName: 'BusLiner Grand Tourer',
  totalSeats: 49,
  rowsCount: 13,
  columnsCount: 4, // 2 кресла слева + 2 кресла справа
  aisleColumnIndex: 2,
  entrances: [
    { id: 'ent-front', side: 'right', row: 1, label: 'Передняя дверь' },
    { id: 'ent-mid', side: 'right', row: 7, label: 'Средняя дверь и лестница' }
  ],
  serviceZones: [
    { id: 'zone-driver', type: 'driver', row: 1, col: 0, colSpan: 2, label: 'Кокпит водителя' },
    { id: 'zone-guide', type: 'coffee', row: 1, col: 2, colSpan: 2, label: 'Место гида / Кухня' },
    { id: 'zone-wc', type: 'wc', row: 7, col: 2, colSpan: 2, label: 'Санузел (WC) и кулер' },
    { id: 'zone-emergency', type: 'emergency-exit', row: 8, col: 3, label: 'Аварийный выход' }
  ],
  seats: [
    // РЯД 2: Панорамный первый ряд (VIP с увеличенным пространством и обзором)
    {
      id: 'c-1', seatNumber: '1', row: 2, col: 0, type: 'panoramic', price: 1650, extraFee: 350,
      status: 'available', features: ['Панорамный вид', 'Увеличенное место для ног', '220V / Type-C'],
      accessibleLabel: 'Место 1, панорамный обзор, у окна слева, 1650 ₽, доступно'
    },
    {
      id: 'c-2', seatNumber: '2', row: 2, col: 1, type: 'panoramic', price: 1550, extraFee: 250,
      status: 'available', features: ['Панорамный вид', 'Увеличенное место для ног', '220V / Type-C'],
      accessibleLabel: 'Место 2, у прохода слева, 1550 ₽, доступно'
    },
    {
      id: 'c-3', seatNumber: '3', row: 2, col: 2, type: 'panoramic', price: 1550, extraFee: 250,
      status: 'occupied', features: ['Панорамный вид', 'Увеличенное место для ног', '220V / Type-C'],
      accessibleLabel: 'Место 3, занято'
    },
    {
      id: 'c-4', seatNumber: '4', row: 2, col: 3, type: 'panoramic', price: 1650, extraFee: 350,
      status: 'occupied', features: ['Панорамный вид', 'Увеличенное место для ног', '220V / Type-C'],
      accessibleLabel: 'Место 4, занято'
    },

    // РЯД 3
    {
      id: 'c-5', seatNumber: '5', row: 3, col: 0, type: 'window', price: 1350, extraFee: 50,
      status: 'available', features: ['У окна', '220V / Type-C', 'Откидной столик'],
      accessibleLabel: 'Место 5, у левого окна, 1350 ₽, доступно'
    },
    {
      id: 'c-6', seatNumber: '6', row: 3, col: 1, type: 'aisle', price: 1300, extraFee: 0,
      status: 'female-only', features: ['Только для женщин', '220V / Type-C'],
      accessibleLabel: 'Место 6, у прохода, женский ряд, 1300 ₽'
    },
    {
      id: 'c-7', seatNumber: '7', row: 3, col: 2, type: 'aisle', price: 1300, extraFee: 0,
      status: 'available', features: ['У прохода', '220V / Type-C'],
      accessibleLabel: 'Место 7, у прохода, 1300 ₽, доступно'
    },
    {
      id: 'c-8', seatNumber: '8', row: 3, col: 3, type: 'window', price: 1350, extraFee: 50,
      status: 'available', features: ['У окна', '220V / Type-C'],
      accessibleLabel: 'Место 8, у правого окна, 1350 ₽, доступно'
    },

    // РЯД 4: Места со столиком (купе для семьи/компании)
    {
      id: 'c-9', seatNumber: '9', row: 4, col: 0, type: 'table', price: 1400, extraFee: 100,
      status: 'available', features: ['Откидной столик', 'Крепление для детского кресла (Isofix)', '220V / Type-C'],
      accessibleLabel: 'Место 9, со столиком и Isofix, 1400 ₽'
    },
    {
      id: 'c-10', seatNumber: '10', row: 4, col: 1, type: 'table', price: 1350, extraFee: 50,
      status: 'available', features: ['Откидной столик', '220V / Type-C'],
      accessibleLabel: 'Место 10, со столиком у прохода, 1350 ₽'
    },
    {
      id: 'c-11', seatNumber: '11', row: 4, col: 2, type: 'aisle', price: 1300, extraFee: 0,
      status: 'disabled', features: ['Спецоборудование для ОВЗ', 'Приоритет для пожилых'],
      accessibleLabel: 'Место 11, приоритетное для пассажиров с инвалидностью, 1300 ₽'
    },
    {
      id: 'c-12', seatNumber: '12', row: 4, col: 3, type: 'window', price: 1350, extraFee: 50,
      status: 'occupied', features: ['У окна'],
      accessibleLabel: 'Место 12, занято'
    },

    // РЯД 5
    {
      id: 'c-13', seatNumber: '13', row: 5, col: 0, type: 'window', price: 1350, extraFee: 50,
      status: 'available', features: ['У окна', '220V / Type-C'],
      accessibleLabel: 'Место 13, 1350 ₽'
    },
    {
      id: 'c-14', seatNumber: '14', row: 5, col: 1, type: 'aisle', price: 1300, extraFee: 0,
      status: 'available', features: ['У прохода', '220V / Type-C'],
      accessibleLabel: 'Место 14, 1300 ₽'
    },
    {
      id: 'c-15', seatNumber: '15', row: 5, col: 2, type: 'aisle', price: 1300, extraFee: 0,
      status: 'male-only', features: ['Только для мужчин'],
      accessibleLabel: 'Место 15, только для мужчин, 1300 ₽'
    },
    {
      id: 'c-16', seatNumber: '16', row: 5, col: 3, type: 'window', price: 1350, extraFee: 50,
      status: 'occupied', features: ['У окна'],
      accessibleLabel: 'Место 16, занято'
    },

    // РЯД 6 (Перед туалетом и средней дверью)
    {
      id: 'c-17', seatNumber: '17', row: 6, col: 0, type: 'window', price: 1350, extraFee: 50,
      status: 'available', features: ['У окна'], accessibleLabel: 'Место 17, 1350 ₽'
    },
    {
      id: 'c-18', seatNumber: '18', row: 6, col: 1, type: 'aisle', price: 1300, extraFee: 0,
      status: 'available', features: ['У прохода'], accessibleLabel: 'Место 18, 1300 ₽'
    },
    {
      id: 'c-19', seatNumber: '19', row: 6, col: 2, type: 'limited-recline', price: 1200, extraFee: -100,
      status: 'available', features: ['Перед туалетом: спинка откидывается не полностью'],
      accessibleLabel: 'Место 19, скидка 100 ₽, 1200 ₽'
    },
    {
      id: 'c-20', seatNumber: '20', row: 6, col: 3, type: 'limited-recline', price: 1200, extraFee: -100,
      status: 'available', features: ['Перед выходом: спинка откидывается не полностью'],
      accessibleLabel: 'Место 20, скидка 100 ₽, 1200 ₽'
    },

    // РЯД 7: Слева места 21, 22. Справа находится блок WC и средняя лестница
    {
      id: 'c-21', seatNumber: '21', row: 7, col: 0, type: 'window', price: 1350, extraFee: 50,
      status: 'available', features: ['У окна'], accessibleLabel: 'Место 21, 1350 ₽'
    },
    {
      id: 'c-22', seatNumber: '22', row: 7, col: 1, type: 'aisle', price: 1300, extraFee: 0,
      status: 'occupied', features: ['У прохода'], accessibleLabel: 'Место 22, занято'
    },

    // РЯД 8: Сразу за средней дверью (Экстра-пространство для ног!)
    {
      id: 'c-23', seatNumber: '23', row: 8, col: 0, type: 'window', price: 1350, extraFee: 50,
      status: 'available', features: ['У окна'], accessibleLabel: 'Место 23, 1350 ₽'
    },
    {
      id: 'c-24', seatNumber: '24', row: 8, col: 1, type: 'aisle', price: 1300, extraFee: 0,
      status: 'available', features: ['У прохода'], accessibleLabel: 'Место 24, 1300 ₽'
    },
    {
      id: 'c-25', seatNumber: '25', row: 8, col: 2, type: 'extra-legroom', price: 1500, extraFee: 200,
      status: 'available', features: ['Увеличенное место для ног', 'Рядом с выходом'],
      accessibleLabel: 'Место 25, увеличенное место для ног, 1500 ₽'
    },
    {
      id: 'c-26', seatNumber: '26', row: 8, col: 3, type: 'extra-legroom', price: 1550, extraFee: 250,
      status: 'available', features: ['Увеличенное место для ног', 'У окна', 'Аварийный выход'],
      accessibleLabel: 'Место 26, у аварийного выхода, 1550 ₽'
    },

    // РЯД 9
    {
      id: 'c-27', seatNumber: '27', row: 9, col: 0, type: 'window', price: 1350, extraFee: 50,
      status: 'blocked', features: ['Заблокировано перевозчиком'], accessibleLabel: 'Место 27, заблокировано'
    },
    {
      id: 'c-28', seatNumber: '28', row: 9, col: 1, type: 'aisle', price: 1300, extraFee: 0,
      status: 'available', features: ['У прохода'], accessibleLabel: 'Место 28, 1300 ₽'
    },
    {
      id: 'c-29', seatNumber: '29', row: 9, col: 2, type: 'aisle', price: 1300, extraFee: 0,
      status: 'available', features: ['У прохода'], accessibleLabel: 'Место 29, 1300 ₽'
    },
    {
      id: 'c-30', seatNumber: '30', row: 9, col: 3, type: 'window', price: 1350, extraFee: 50,
      status: 'available', features: ['У окна'], accessibleLabel: 'Место 30, 1350 ₽'
    },

    // РЯД 10
    {
      id: 'c-31', seatNumber: '31', row: 10, col: 0, type: 'window', price: 1350, extraFee: 50,
      status: 'occupied', features: ['У окна'], accessibleLabel: 'Место 31, занято'
    },
    {
      id: 'c-32', seatNumber: '32', row: 10, col: 1, type: 'aisle', price: 1300, extraFee: 0,
      status: 'occupied', features: ['У прохода'], accessibleLabel: 'Место 32, занято'
    },
    {
      id: 'c-33', seatNumber: '33', row: 10, col: 2, type: 'aisle', price: 1300, extraFee: 0,
      status: 'available', features: ['У прохода'], accessibleLabel: 'Место 33, 1300 ₽'
    },
    {
      id: 'c-34', seatNumber: '34', row: 10, col: 3, type: 'window', price: 1350, extraFee: 50,
      status: 'available', features: ['У окна'], accessibleLabel: 'Место 34, 1350 ₽'
    },

    // РЯД 11
    {
      id: 'c-35', seatNumber: '35', row: 11, col: 0, type: 'window', price: 1300, extraFee: 0,
      status: 'available', features: ['У окна'], accessibleLabel: 'Место 35, 1300 ₽'
    },
    {
      id: 'c-36', seatNumber: '36', row: 11, col: 1, type: 'aisle', price: 1300, extraFee: 0,
      status: 'available', features: ['У прохода'], accessibleLabel: 'Место 36, 1300 ₽'
    },
    {
      id: 'c-37', seatNumber: '37', row: 11, col: 2, type: 'aisle', price: 1300, extraFee: 0,
      status: 'female-only', features: ['Женский ряд'], accessibleLabel: 'Место 37, только для женщин, 1300 ₽'
    },
    {
      id: 'c-38', seatNumber: '38', row: 11, col: 3, type: 'window', price: 1300, extraFee: 0,
      status: 'female-only', features: ['Женский ряд', 'У окна'], accessibleLabel: 'Место 38, только для женщин, 1300 ₽'
    },

    // РЯД 12
    {
      id: 'c-39', seatNumber: '39', row: 12, col: 0, type: 'window', price: 1250, extraFee: -50,
      status: 'available', features: ['У окна'], accessibleLabel: 'Место 39, 1250 ₽'
    },
    {
      id: 'c-40', seatNumber: '40', row: 12, col: 1, type: 'aisle', price: 1250, extraFee: -50,
      status: 'available', features: ['У прохода'], accessibleLabel: 'Место 40, 1250 ₽'
    },
    {
      id: 'c-41', seatNumber: '41', row: 12, col: 2, type: 'aisle', price: 1250, extraFee: -50,
      status: 'available', features: ['У прохода'], accessibleLabel: 'Место 41, 1250 ₽'
    },
    {
      id: 'c-42', seatNumber: '42', row: 12, col: 3, type: 'window', price: 1250, extraFee: -50,
      status: 'available', features: ['У окна'], accessibleLabel: 'Место 42, 1250 ₽'
    },

    // РЯД 13 (Задний диван на 5 кресел, ограниченный наклон спинки, выгодная цена)
    {
      id: 'c-45', seatNumber: '45', row: 13, col: 0, type: 'limited-recline', price: 1100, extraFee: -200,
      status: 'available', features: ['Не откидывается спинка', 'Эконом-цена'], accessibleLabel: 'Место 45, задний ряд, 1100 ₽'
    },
    {
      id: 'c-46', seatNumber: '46', row: 13, col: 1, type: 'limited-recline', price: 1100, extraFee: -200,
      status: 'available', features: ['Не откидывается спинка'], accessibleLabel: 'Место 46, задний ряд, 1100 ₽'
    },
    {
      id: 'c-47', seatNumber: '47', row: 13, col: 2, type: 'limited-recline', price: 1050, extraFee: -250,
      status: 'available', features: ['Центральное место', 'Не откидывается спинка'], accessibleLabel: 'Место 47, задний ряд центр, 1050 ₽'
    },
    {
      id: 'c-48', seatNumber: '48', row: 13, col: 3, type: 'limited-recline', price: 1100, extraFee: -200,
      status: 'available', features: ['Не откидывается спинка'], accessibleLabel: 'Место 48, задний ряд, 1100 ₽'
    },
    {
      id: 'c-49', seatNumber: '49', row: 13, col: 4, type: 'limited-recline', price: 1100, extraFee: -200,
      status: 'available', features: ['Не откидывается спинка', 'Эконом-цена'], accessibleLabel: 'Место 49, задний ряд, 1100 ₽'
    }
  ]
};
