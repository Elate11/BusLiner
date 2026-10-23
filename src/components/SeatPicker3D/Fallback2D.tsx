import React, { useMemo } from 'react';
import { useSeatStore } from './useSeatStore';
import { SeatData3D } from './types';
import styles from './SeatPicker3D.module.css';

export const Fallback2D: React.FC = () => {
  const seats = useSeatStore((s) => s.seats);
  const selectedSeatIds = useSeatStore((s) => s.selectedSeatIds);
  const toggleSeat = useSeatStore((s) => s.toggleSeat);

  // Группировка мест по рядам
  const rows = useMemo(() => {
    const rowMap = new Map<number, SeatData3D[]>();
    seats.forEach((seat) => {
      const list = rowMap.get(seat.row) || [];
      list.push(seat);
      rowMap.set(seat.row, list);
    });
    return Array.from(rowMap.entries()).sort(([a], [b]) => a - b);
  }, [seats]);

  const handleKeyDown = (e: React.KeyboardEvent, seat: SeatData3D) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      if (seat.status === 'available') {
        toggleSeat(seat.id);
      }
    }
  };

  return (
    <div className={styles.fallbackContainer} role="region" aria-label="Схема выбора места (2D доступный режим)">
      <div className={styles.fallbackCard}>
        <div className={styles.fallbackHeader}>
          <h3 className={styles.fallbackTitle}>Доступная схема салона</h3>
          <p className={styles.fallbackSubtitle}>
            Используйте клавиши Tab для перехода между местами, клавишу Пробел или Enter для выбора места.
          </p>
        </div>

        <div className={styles.gridSalon}>
          {rows.map(([rowNum, rowSeats]) => (
            <div key={rowNum} className={styles.gridRow}>
              <div className={styles.rowLabel}>Ряд {rowNum}</div>
              <div className={styles.seatsInRow}>
                {rowSeats.map((seat) => {
                  const isSelected = selectedSeatIds.includes(seat.id);
                  const isAvailable = seat.status === 'available';
                  const isOccupied = seat.status === 'occupied';
                  const isBlocked = seat.status === 'blocked';
                  const isDisabled = seat.status === 'disabled';

                  let statusText = 'Доступно';
                  if (isOccupied) statusText = 'Занято другим пассажиром';
                  if (isBlocked) statusText = 'Заблокировано перевозчиком';
                  if (isDisabled) statusText = 'Для пассажиров с ОВЗ';
                  if (isSelected) statusText = 'Выбрано вами';

                  return (
                    <button
                      key={seat.id}
                      type="button"
                      role="checkbox"
                      aria-checked={isSelected}
                      aria-disabled={!isAvailable}
                      disabled={!isAvailable}
                      className={`${styles.seat2DButton} ${isSelected ? styles.seat2DSelected : ''} ${
                        !isAvailable ? styles.seat2DDisabled : ''
                      }`}
                      onClick={() => isAvailable && toggleSeat(seat.id)}
                      onKeyDown={(e) => handleKeyDown(e, seat)}
                      aria-label={`Место ${seat.number}, категория ${seat.category}, стоимость ${seat.price} рублей, статус: ${statusText}`}
                    >
                      <span className={styles.seat2DNumber}>{seat.number}</span>
                      <span className={styles.seat2DPrice}>{seat.price} ₽</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
