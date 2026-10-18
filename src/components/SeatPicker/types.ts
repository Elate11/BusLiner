/**
 * Типы данных компонента выбора места в салоне (SeatPicker)
 * Разработано по стандартам travel-tech (FlixBus, Aviasales, Omio)
 */

export type SeatStatus =
  | 'available'    // Доступно для бронирования
  | 'selected'     // Выбрано текущим пользователем
  | 'occupied'     // Занято другим пассажиром
  | 'blocked'      // Заблокировано перевозчиком / служебное
  | 'female-only'  // Место только для женщин
  | 'male-only'    // Место только для мужчин
  | 'disabled';    // Специальное место для маломобильных граждан (ОВЗ)

export type SeatType =
  | 'standard'         // Стандартное комфортное место
  | 'window'           // Место у окна
  | 'aisle'            // Место у прохода
  | 'extra-legroom'    // Увеличенное пространство для ног (первые ряды, аварийный выход)
  | 'limited-recline'  // Ограниченный наклон спинки (последний ряд / перед туалетом)
  | 'panoramic'        // Панорамный вид (первый ряд второго этажа или лобовое стекло)
  | 'table';           // Место со стационарным столиком

export type SeatFeature =
  | '220V / Type-C'
  | 'Увеличенное место для ног'
  | 'Не откидывается спинка'
  | 'Откидной столик'
  | 'Панорамный вид'
  | 'Рядом с выходом'
  | 'Индивидуальный обдув и свет'
  | 'Подставка для ног'
  | 'Крепление для детского кресла (Isofix)'
  | 'Спецоборудование для ОВЗ';

export interface SeatData {
  id: string;               // Уникальный ID (например, '1A', '12B')
  seatNumber: string;       // Номер кресла, видимый пассажиру ('12', '1A')
  row: number;              // Номер ряда (1-indexed)
  col: number;              // Номер колонки по ширине салона (0-indexed)
  type: SeatType;           // Категория места
  price: number;            // Полная стоимость места (билет + надбавка)
  extraFee: number;         // Надбавка за категорию места (0 если стандарт)
  status: SeatStatus;       // Текущий статус доступности
  features: SeatFeature[];  // Особенности кресла
  accessibleLabel?: string; // Текст для скринридеров (a11y)
}

export type ServiceZoneType = 'wc' | 'stairs' | 'luggage' | 'coffee' | 'driver' | 'emergency-exit';

export interface ServiceZone {
  id: string;
  type: ServiceZoneType;
  row: number;
  col: number;
  colSpan?: number;
  rowSpan?: number;
  label: string;
  icon?: string;
}

export interface VehicleEntrance {
  id: string;
  side: 'left' | 'right';
  row: number;
  label: string;
}

export interface VehicleLayout {
  id: string;
  type: 'minibus_2_1' | 'coach_2_2';
  name: string;             // Например: "Mercedes Sprinter Tourer (19 мест)" или "Scania Touring 12M (49 мест)"
  carrierName: string;
  totalSeats: number;
  rowsCount: number;
  columnsCount: number;     // 3 для 2+1, 4 для 2+2 (+ проход учитывается в сетке)
  aisleColumnIndex: number; // Индекс колонки прохода (для 2+1 это 1, для 2+2 это 2)
  seats: SeatData[];
  serviceZones: ServiceZone[];
  entrances: VehicleEntrance[];
}

export interface SeatPickerProps {
  layout: VehicleLayout;
  maxSeats?: number;              // Лимит мест (по числу пассажиров в заказе)
  initialSelectedSeatIds?: string[];
  currency?: string;              // '₽', 'BYN', '€'
  onSelectionChange?: (selectedSeats: SeatData[]) => void;
  onProceed?: (selectedSeats: SeatData[]) => void;
  className?: string;
}
