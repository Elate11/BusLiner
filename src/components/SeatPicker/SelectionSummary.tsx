import React from 'react';
import { SeatData } from './types';
import styles from './SeatPicker.module.css';

interface SelectionSummaryProps {
  selectedSeats: SeatData[];
  maxSeats: number;
  currency?: string;
  onRemoveSeat: (seatId: string) => void;
  onProceed?: (selectedSeats: SeatData[]) => void;
  limitNotice: string | null;
}

export const SelectionSummary: React.FC<SelectionSummaryProps> = ({
  selectedSeats,
  maxSeats,
  currency = '₽',
  onRemoveSeat,
  onProceed,
  limitNotice
}) => {
  const count = selectedSeats.length;
  const totalPrice = selectedSeats.reduce((sum, s) => sum + s.price, 0);

  const formatSeatsText = (num: number) => {
    if (num % 10 === 1 && num % 100 !== 11) return `${num} место`;
    if ([2, 3, 4].includes(num % 10) && ![12, 13, 14].includes(num % 100)) return `${num} места`;
    return `${num} мест`;
  };

  return (
    <footer className={styles.summaryStickyBar} aria-label="Панель итогового выбора мест">
      {/* Мягкое уведомление о лимите мест без alert() */}
      {limitNotice && (
        <div className={styles.limitBanner} role="status" aria-live="polite">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{limitNotice}</span>
        </div>
      )}

      <div className={styles.summaryContainer}>
        {/* Левая секция: Выбранные места и расчет суммы */}
        <div className={styles.summaryDetails}>
          {count === 0 ? (
            <div className={styles.summaryEmptyState}>
              <div className={styles.summaryEmptyIcon}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="4" width="18" height="16" rx="3" />
                  <path d="M3 10h18M7 15h.01M17 15h.01" />
                </svg>
              </div>
              <div>
                <p className={styles.summaryEmptyTitle}>Выберите место на схеме</p>
                <p className={styles.summaryEmptySubtitle}>
                  Пассажиров в заказе: {maxSeats} &bull; Выберите до {maxSeats} мест
                </p>
              </div>
            </div>
          ) : (
            <div>
              <div className={styles.summaryHeader}>
                <span className={styles.summaryCount}>
                  Выбрано {formatSeatsText(count)} из {maxSeats}:
                </span>
                <span className={styles.summaryTotalPrice}>
                  {totalPrice.toLocaleString('ru-RU')} {currency}
                </span>
              </div>

              {/* Теги выбранных мест с возможностью быстрого снятия */}
              <div className={styles.summaryChipsList} role="list" aria-label="Список выбранных мест">
                {selectedSeats.map(seat => (
                  <span key={seat.id} className={styles.summaryChip} role="listitem">
                    <span className={styles.summaryChipText}>
                      Место {seat.seatNumber} &bull; {seat.price} {currency}
                    </span>
                    <button
                      type="button"
                      className={styles.summaryChipRemoveBtn}
                      onClick={() => onRemoveSeat(seat.id)}
                      aria-label={`Удалить место ${seat.seatNumber}`}
                      title="Отменить выбор места"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Правая секция: Главный CTA */}
        <div className={styles.summaryAction}>
          <button
            type="button"
            className={styles.summaryProceedBtn}
            disabled={count === 0}
            onClick={() => onProceed && onProceed(selectedSeats)}
          >
            <span>Продолжить бронирование</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </div>
      </div>
    </footer>
  );
};
