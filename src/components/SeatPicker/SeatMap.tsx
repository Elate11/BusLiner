import React, { useRef, useState, useEffect } from 'react';
import { VehicleLayout, SeatData } from './types';
import { Seat } from './Seat';
import { Tooltip } from './Tooltip';
import styles from './SeatPicker.module.css';

interface SeatMapProps {
  layout: VehicleLayout;
  selectedSeatIds: string[];
  currency?: string;
  onSeatToggle: (seat: SeatData) => void;
}

export const SeatMap: React.FC<SeatMapProps> = ({
  layout,
  selectedSeatIds,
  currency = '₽',
  onSeatToggle
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapGridRef = useRef<HTMLDivElement>(null);

  // Состояние тултипа
  const [activeTooltip, setActiveTooltip] = useState<{
    seat: SeatData | null;
    rect: DOMRect | null;
    visible: boolean;
  }>({
    seat: null,
    rect: null,
    visible: false
  });

  const [containerRect, setContainerRect] = useState<DOMRect | null>(null);

  const updateContainerRect = () => {
    if (containerRef.current) {
      setContainerRect(containerRef.current.getBoundingClientRect());
    }
  };

  useEffect(() => {
    updateContainerRect();
    window.addEventListener('resize', updateContainerRect);
    return () => window.removeEventListener('resize', updateContainerRect);
  }, []);

  const handleHoverStart = (seat: SeatData, rect: DOMRect) => {
    updateContainerRect();
    setActiveTooltip({ seat, rect, visible: true });
  };

  const handleHoverEnd = () => {
    setActiveTooltip(prev => ({ ...prev, visible: false }));
  };

  // 2D Клавиатурная навигация стрелками (стрелки вверх/вниз/влево/вправо)
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) return;

    const focusedEl = document.activeElement as HTMLElement;
    if (!focusedEl || !mapGridRef.current?.contains(focusedEl)) return;

    const allInteractiveSeats = Array.from(
      mapGridRef.current.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')
    );

    const currentIndex = allInteractiveSeats.indexOf(focusedEl as HTMLButtonElement);
    if (currentIndex === -1) return;

    e.preventDefault();

    let targetIndex = currentIndex;
    const is2Plus1 = layout.type === 'minibus_2_1';
    const rowStep = is2Plus1 ? 3 : 4; // примерный шаг строки для вертикального перемещения

    switch (e.key) {
      case 'ArrowRight':
        targetIndex = Math.min(allInteractiveSeats.length - 1, currentIndex + 1);
        break;
      case 'ArrowLeft':
        targetIndex = Math.max(0, currentIndex - 1);
        break;
      case 'ArrowDown':
        targetIndex = Math.min(allInteractiveSeats.length - 1, currentIndex + rowStep);
        break;
      case 'ArrowUp':
        targetIndex = Math.max(0, currentIndex - rowStep);
        break;
    }

    if (allInteractiveSeats[targetIndex]) {
      allInteractiveSeats[targetIndex].focus();
    }
  };

  // Группировка кресел по рядам
  const rowsMap = new Map<number, SeatData[]>();
  for (let r = 1; r <= layout.rowsCount; r++) {
    rowsMap.set(r, []);
  }
  layout.seats.forEach(seat => {
    const list = rowsMap.get(seat.row) || [];
    list.push(seat);
    rowsMap.set(seat.row, list);
  });

  return (
    <div
      ref={containerRef}
      className={styles.seatMapWrapper}
      onKeyDown={handleKeyDown}
      role="region"
      aria-label={`Схема салона: ${layout.name}`}
    >
      {/* Тултип с автопозиционированием */}
      <Tooltip
        seat={activeTooltip.seat}
        targetRect={activeTooltip.rect}
        containerRect={containerRect}
        currency={currency}
        visible={activeTooltip.visible}
      />

      {/* Горизонтальный скролл-контейнер для мобильных устройств */}
      <div className={styles.seatMapScrollArea}>
        <div ref={mapGridRef} className={styles.busHull}>
          
          {/* ================= НОСОВАЯ ЧАСТЬ / КАБИНА ================= */}
          <header className={styles.busFrontHeader}>
            {/* Очертания лобового стекла и зеркал */}
            <div className={styles.busWindshield}>
              <span className={styles.windshieldWiperLeft} />
              <span className={styles.windshieldWiperRight} />
              <span className={styles.busFrontLabel}>
                {layout.carrierName} &bull; Направление движения &rarr;
              </span>
            </div>

            {/* Зона водителя и передней двери */}
            <div className={styles.frontCockpitRow}>
              {/* Кабина водителя (слева) */}
              <div className={styles.driverCockpit}>
                <div className={styles.steeringWheel}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <circle cx="12" cy="12" r="3" />
                    <line x1="2" y1="12" x2="9" y2="12" />
                    <line x1="15" y1="12" x2="22" y2="12" />
                    <line x1="12" y1="15" x2="12" y2="22" />
                  </svg>
                </div>
                <span className={styles.driverLabel}>Водитель</span>
              </div>

              {/* Проход между кабиной и входом */}
              <div className={styles.frontCockpitAisle} />

              {/* Посадочная дверь со ступенями (справа) */}
              <div className={styles.entranceDoor}>
                <div className={styles.entranceStairs}>
                  <span className={styles.stairStep} />
                  <span className={styles.stairStep} />
                </div>
                <div className={styles.entranceMeta}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                  <span>Вход</span>
                </div>
              </div>
            </div>
          </header>

          {/* ================= ПАССАЖИРСКИЙ САЛОН ================= */}
          <main className={styles.cabinSaloon} role="grid" aria-label="Пассажирские кресла">
            {Array.from(rowsMap.entries()).map(([rowNum, seatsInRow]) => {
              // Проверяем служебные зоны на этом ряду (туалет, средняя дверь и т.д.)
              const zoneInRow = layout.serviceZones.find(z => z.row === rowNum && z.type !== 'driver');
              const entranceInRow = layout.entrances.find(e => e.row === rowNum && e.row !== 1);

              return (
                <div key={rowNum} className={styles.cabinRow} role="row">
                  {/* Номер ряда для удобства ориентации */}
                  <span className={styles.rowNumberIndicator} aria-hidden="true">
                    {rowNum}
                  </span>

                  {/* Сетка кресел ряда */}
                  <div className={styles.rowSeatsGroup}>
                    {/* Левый борт кресел (колонки до прохода) */}
                    <div className={styles.sidePair}>
                      {seatsInRow
                        .filter(s => s.col < layout.aisleColumnIndex)
                        .map(seat => (
                          <Seat
                            key={seat.id}
                            seat={seat}
                            isSelected={selectedSeatIds.includes(seat.id)}
                            currency={currency}
                            onSelect={onSeatToggle}
                            onHoverStart={handleHoverStart}
                            onHoverEnd={handleHoverEnd}
                          />
                        ))}
                    </div>

                    {/* Центральный проход с подсветкой */}
                    <div className={styles.aisleTrack} aria-hidden="true">
                      <span className={styles.aisleDottedLine} />
                    </div>

                    {/* Правый борт кресел или служебный блок (туалет, лестница) */}
                    <div className={styles.sidePair}>
                      {zoneInRow && zoneInRow.type === 'wc' ? (
                        <div className={styles.serviceZoneWc} title="Санузел (WC) на борту">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="3" y="3" width="18" height="18" rx="4" />
                            <circle cx="12" cy="9" r="2.5" />
                            <path d="M9 18v-3a3 3 0 0 1 6 0v3" />
                          </svg>
                          <span>WC</span>
                        </div>
                      ) : entranceInRow ? (
                        <div className={styles.midEntrance} title="Средняя посадочная дверь">
                          <span>Вход 2</span>
                        </div>
                      ) : (
                        seatsInRow
                          .filter(s => s.col >= layout.aisleColumnIndex)
                          .map(seat => (
                            <Seat
                              key={seat.id}
                              seat={seat}
                              isSelected={selectedSeatIds.includes(seat.id)}
                              currency={currency}
                              onSelect={onSeatToggle}
                              onHoverStart={handleHoverStart}
                              onHoverEnd={handleHoverEnd}
                            />
                          ))
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </main>

          {/* ================= КОРМА / БАГАЖНЫЙ ОТСЕК ================= */}
          <footer className={styles.busRearLuggage}>
            <div className={styles.luggageCompartment}>
              <div className={styles.luggageIcon}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="7" width="20" height="14" rx="2" />
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                </svg>
              </div>
              <div className={styles.luggageText}>
                <span className={styles.luggageTitle}>Багажное отделение</span>
                <span className={styles.luggageSub}>До 2 мест багажа включено в билет</span>
              </div>
            </div>
            {/* Распашные задние двери */}
            <div className={styles.busRearBumper} />
          </footer>

        </div>
      </div>
    </div>
  );
};
