import React, { useRef } from 'react';
import { SeatData } from './types';
import styles from './SeatPicker.module.css';

interface SeatProps {
  seat: SeatData;
  isSelected: boolean;
  currency?: string;
  onSelect: (seat: SeatData) => void;
  onHoverStart: (seat: SeatData, rect: DOMRect) => void;
  onHoverEnd: () => void;
}

export const Seat: React.FC<SeatProps> = ({
  seat,
  isSelected,
  currency = '₽',
  onSelect,
  onHoverStart,
  onHoverEnd
}) => {
  const seatRef = useRef<HTMLButtonElement>(null);
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isInteractive = seat.status !== 'occupied' && seat.status !== 'blocked';

  const handleClick = () => {
    if (!isInteractive) return;
    onSelect(seat);
  };

  const handleMouseEnter = () => {
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = setTimeout(() => {
      if (seatRef.current) {
        onHoverStart(seat, seatRef.current.getBoundingClientRect());
      }
    }, 320); // 320мс дебаунс по ТЗ (300-400мс)
  };

  const handleMouseLeave = () => {
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }
    onHoverEnd();
  };

  const handleFocus = () => {
    if (seatRef.current) {
      onHoverStart(seat, seatRef.current.getBoundingClientRect());
    }
  };

  const handleBlur = () => {
    onHoverEnd();
  };

  // Построение a11y label
  const getAriaLabel = () => {
    if (seat.accessibleLabel) return seat.accessibleLabel;
    const statusText = isSelected
      ? 'выбрано вами'
      : seat.status === 'occupied'
      ? 'занято'
      : seat.status === 'blocked'
      ? 'недоступно'
      : 'доступно';
    return `Место ${seat.seatNumber}, ряд ${seat.row}, ${seat.price} ${currency}, ${statusText}`;
  };

  // CSS классы статуса
  const statusClass = isSelected
    ? styles.seat_selected
    : styles[`seat_${seat.status}`] || styles.seat_available;

  const typeClass = styles[`seat_type_${seat.type}`] || '';

  return (
    <button
      ref={seatRef}
      type="button"
      className={`${styles.seat} ${statusClass} ${typeClass}`}
      disabled={!isInteractive}
      aria-label={getAriaLabel()}
      aria-pressed={isSelected}
      aria-disabled={!isInteractive}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
      tabIndex={isInteractive ? 0 : -1}
    >
      {/* Спинка сиденья с контуром подголовника */}
      <span className={styles.seatBackrest}>
        <span className={styles.seatHeadrest} />
      </span>

      {/* Подушка сиденья и номер */}
      <span className={styles.seatCushion}>
        <span className={styles.seatNumber}>{seat.seatNumber}</span>

        {/* Индикатор пола или ОВЗ */}
        {seat.status === 'disabled' && (
          <span className={styles.seatIconBadge} title="Место для маломобильных граждан">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="4" r="2" />
              <path d="M19 13v-2a4 4 0 0 0-4-4h-3a4 4 0 0 0-4 4v7" />
              <circle cx="9" cy="18" r="3" />
            </svg>
          </span>
        )}

        {seat.status === 'female-only' && (
          <span className={styles.seatIconBadge} title="Только для женщин">
            <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="8" r="5" />
              <line x1="12" y1="13" x2="12" y2="21" />
              <line x1="9" y1="17" x2="15" y2="17" />
            </svg>
          </span>
        )}

        {seat.status === 'male-only' && (
          <span className={styles.seatIconBadge} title="Только для мужчин">
            <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="10" cy="14" r="5" />
              <line x1="19" y1="5" x2="13.6" y2="10.4" />
              <polyline points="14 5 19 5 19 10" />
            </svg>
          </span>
        )}

        {/* Индикатор надбавки или скидки за место */}
        {seat.extraFee !== 0 && seat.status === 'available' && !isSelected && (
          <span className={seat.extraFee > 0 ? styles.seatFeeDotPlus : styles.seatFeeDotMinus} />
        )}
      </span>

      {/* Контурные подлокотники */}
      <span className={styles.seatArmrestLeft} />
      <span className={styles.seatArmrestRight} />
    </button>
  );
};
