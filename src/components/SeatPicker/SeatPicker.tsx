import React, { useState, useEffect } from 'react';
import { VehicleLayout, SeatData, SeatPickerProps } from './types';
import { SeatMap } from './SeatMap';
import { Legend } from './Legend';
import { SelectionSummary } from './SelectionSummary';
import { minibus19MockLayout, coach49MockLayout } from './mockData';
import styles from './SeatPicker.module.css';

export interface StandaloneSeatPickerProps extends Partial<SeatPickerProps> {
  allowVehicleSwitch?: boolean;
}

export const SeatPicker: React.FC<StandaloneSeatPickerProps> = ({
  layout: initialLayout,
  maxSeats = 2,
  initialSelectedSeatIds = [],
  currency = '₽',
  allowVehicleSwitch = true,
  onSelectionChange,
  onProceed
}) => {
  // Выбранный макет ТС (по умолчанию микроавтобус BusLiner или переданный через props)
  const [currentLayout, setCurrentLayout] = useState<VehicleLayout>(
    initialLayout || minibus19MockLayout
  );

  // Выбранные места
  const [selectedSeats, setSelectedSeats] = useState<SeatData[]>(() => {
    if (initialSelectedSeatIds.length === 0) return [];
    return currentLayout.seats.filter(s => initialSelectedSeatIds.includes(s.id));
  });

  // Мягкое уведомление об ограничении лимита мест (без alert)
  const [limitNotice, setLimitNotice] = useState<string | null>(null);

  // Состояние загрузки (skeleton)
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Сброс выбора при смене типа ТС
  const handleVehicleSwitch = (layoutKey: 'minibus' | 'coach') => {
    setIsLoading(true);
    setSelectedSeats([]);
    setLimitNotice(null);

    setTimeout(() => {
      setCurrentLayout(layoutKey === 'minibus' ? minibus19MockLayout : coach49MockLayout);
      setIsLoading(false);
    }, 280); // реалистичный отклик смены борта
  };

  // Обработка клика по креслу
  const handleSeatToggle = (seat: SeatData) => {
    setLimitNotice(null);

    const isAlreadySelected = selectedSeats.some(s => s.id === seat.id);

    if (isAlreadySelected) {
      // Снятие выбора
      const updated = selectedSeats.filter(s => s.id !== seat.id);
      setSelectedSeats(updated);
      onSelectionChange?.(updated);
    } else {
      // Проверка лимита мест
      if (selectedSeats.length >= maxSeats) {
        setLimitNotice(
          `Выбрано максимальное количество мест (${maxSeats} из ${maxSeats}). Снимите выбор с одного из мест, чтобы выбрать другое.`
        );
        return;
      }

      // Добавление места
      const updated = [...selectedSeats, seat];
      setSelectedSeats(updated);
      onSelectionChange?.(updated);
    }
  };

  const handleRemoveSeat = (seatId: string) => {
    const updated = selectedSeats.filter(s => s.id !== seatId);
    setSelectedSeats(updated);
    setLimitNotice(null);
    onSelectionChange?.(updated);
  };

  // Таймер автоскрытия мягкого уведомления
  useEffect(() => {
    if (!limitNotice) return;
    const timer = setTimeout(() => {
      setLimitNotice(null);
    }, 4500);
    return () => clearTimeout(timer);
  }, [limitNotice]);

  return (
    <div className={styles.seatPickerCard}>
      {/* ================= ШАПКА ВЫБОРА МЕСТ ================= */}
      <header className={styles.pickerHeader}>
        <div>
          <div className={styles.carrierTagline}>
            <span className={styles.carrierTagBadge}>Шаг 2 из 3 &bull; Рассадка</span>
            <span className={styles.carrierName}>{currentLayout.carrierName}</span>
          </div>
          <h2 className={styles.pickerTitle}>Выбор места в салоне</h2>
          <p className={styles.pickerSubtitle}>
            {currentLayout.name} &bull; {currentLayout.totalSeats} мест &bull;{' '}
            {currentLayout.type === 'minibus_2_1' ? 'Компоновка 2+1' : 'Компоновка 2+2 (Турист)'}
          </p>
        </div>

        {/* Переключатель типа ТС (демонстрация универсальности) */}
        {allowVehicleSwitch && (
          <div className={styles.vehicleSwitcher} role="group" aria-label="Переключение типа салона">
            <button
              type="button"
              className={`${styles.switchBtn} ${currentLayout.type === 'minibus_2_1' ? styles.switchBtn_active : ''}`}
              onClick={() => handleVehicleSwitch('minibus')}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="5" width="20" height="14" rx="3" />
                <path d="M7 15h.01M17 15h.01" />
              </svg>
              <span>Микроавтобус (19 мест, 2+1)</span>
            </button>

            <button
              type="button"
              className={`${styles.switchBtn} ${currentLayout.type === 'coach_2_2' ? styles.switchBtn_active : ''}`}
              onClick={() => handleVehicleSwitch('coach')}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="4" width="20" height="16" rx="3" />
                <path d="M2 10h20M6 16h.01M18 16h.01" />
              </svg>
              <span>Лайнер дальнего следования (49 мест, 2+2)</span>
            </button>
          </div>
        )}
      </header>

      {/* ================= КОМПАКТНАЯ ЛЕГЕНДА ================= */}
      <Legend />

      {/* ================= ОСНОВНОЙ САЛОН / SKELETON ================= */}
      {isLoading ? (
        <div className={styles.skeletonContainer} aria-busy="true" aria-label="Загрузка схемы салона">
          <div className={styles.skeletonHull}>
            <div className={styles.skeletonHeader} />
            <div className={styles.skeletonRows}>
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className={styles.skeletonRow} />
              ))}
            </div>
          </div>
        </div>
      ) : (
        <SeatMap
          layout={currentLayout}
          selectedSeatIds={selectedSeats.map(s => s.id)}
          currency={currency}
          onSeatToggle={handleSeatToggle}
        />
      )}

      {/* ================= STICKY ПАНЕЛЬ ИТОГА ================= */}
      <SelectionSummary
        selectedSeats={selectedSeats}
        maxSeats={maxSeats}
        currency={currency}
        onRemoveSeat={handleRemoveSeat}
        onProceed={onProceed}
        limitNotice={limitNotice}
      />
    </div>
  );
};

export default SeatPicker;
