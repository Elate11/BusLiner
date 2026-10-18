import React, { useEffect, useRef, useState } from 'react';
import { SeatData } from './types';
import styles from './SeatPicker.module.css';

interface TooltipProps {
  seat: SeatData | null;
  targetRect: DOMRect | null;
  containerRect: DOMRect | null;
  currency?: string;
  visible: boolean;
}

export const Tooltip: React.FC<TooltipProps> = ({
  seat,
  targetRect,
  containerRect,
  currency = '₽',
  visible
}) => {
  const [coords, setCoords] = useState<{ top: number; left: number; placement: 'top' | 'bottom' }>({
    top: 0,
    left: 0,
    placement: 'top'
  });

  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!visible || !targetRect || !containerRect || !tooltipRef.current) return;

    const tooltipEl = tooltipRef.current;
    const tooltipWidth = tooltipEl.offsetWidth || 220;
    const tooltipHeight = tooltipEl.offsetHeight || 110;

    // Вычисляем координаты относительно контейнера схемы
    const targetCenterX = targetRect.left - containerRect.left + targetRect.width / 2;
    let left = targetCenterX - tooltipWidth / 2;

    // Защита от выхода за левый и правый края контейнера
    if (left < 8) left = 8;
    if (left + tooltipWidth > containerRect.width - 8) {
      left = containerRect.width - tooltipWidth - 8;
    }

    // Проверяем, помещается ли тултип сверху
    const spaceTop = targetRect.top - containerRect.top;
    let top = 0;
    let placement: 'top' | 'bottom' = 'top';

    if (spaceTop >= tooltipHeight + 12) {
      top = targetRect.top - containerRect.top - tooltipHeight - 10;
      placement = 'top';
    } else {
      // Иначе открываем снизу
      top = targetRect.bottom - containerRect.top + 10;
      placement = 'bottom';
    }

    setCoords({ top, left, placement });
  }, [visible, targetRect, containerRect, seat]);

  if (!seat || !visible) return null;

  const getTypeLabel = (type: SeatData['type']) => {
    switch (type) {
      case 'panoramic': return 'Панорамный обзор';
      case 'extra-legroom': return 'Больше места для ног';
      case 'table': return 'Место со столиком';
      case 'limited-recline': return 'Ограниченный наклон';
      case 'window': return 'У окна';
      case 'aisle': return 'У прохода';
      default: return 'Стандартное место';
    }
  };

  const getStatusNotice = (status: SeatData['status']) => {
    switch (status) {
      case 'female-only': return 'Только для пассажиров женского пола';
      case 'male-only': return 'Только для пассажиров мужского пола';
      case 'disabled': return 'Приоритет для маломобильных граждан';
      case 'blocked': return 'Заблокировано перевозчиком';
      case 'occupied': return 'Место уже занято';
      default: return null;
    }
  };

  const statusNotice = getStatusNotice(seat.status);

  return (
    <div
      ref={tooltipRef}
      className={`${styles.tooltip} ${styles[`tooltip_${coords.placement}`]}`}
      style={{
        transform: `translate3d(${Math.round(coords.left)}px, ${Math.round(coords.top)}px, 0)`,
        opacity: visible ? 1 : 0
      }}
      role="tooltip"
      aria-hidden="true"
    >
      <div className={styles.tooltipHeader}>
        <div className={styles.tooltipTitle}>
          <span className={styles.tooltipSeatNum}>Место {seat.seatNumber}</span>
          <span className={styles.tooltipTypeBadge}>{getTypeLabel(seat.type)}</span>
        </div>
        <div className={styles.tooltipPrice}>
          {seat.price} {currency}
          {seat.extraFee > 0 && <span className={styles.tooltipExtraFee}>+{seat.extraFee} {currency}</span>}
          {seat.extraFee < 0 && <span className={styles.tooltipDiscountFee}>{seat.extraFee} {currency}</span>}
        </div>
      </div>

      {statusNotice && (
        <div className={styles.tooltipStatusNotice}>
          {statusNotice}
        </div>
      )}

      {seat.features.length > 0 && (
        <ul className={styles.tooltipFeatures}>
          {seat.features.map((feat, idx) => (
            <li key={idx} className={styles.tooltipFeatureItem}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>{feat}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
