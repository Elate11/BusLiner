import React, { useMemo } from 'react';
import { useSeatStore } from './useSeatStore';
import { CameraPreset } from './types';
import styles from './SeatPicker3D.module.css';

export const UIOverlay: React.FC = () => {
  const currentVehicle = useSeatStore((s) => s.currentVehicle);
  const seats = useSeatStore((s) => s.seats);
  const selectedSeatIds = useSeatStore((s) => s.selectedSeatIds);
  const activePreset = useSeatStore((s) => s.activePreset);
  const notification = useSeatStore((s) => s.notification);
  const is2DFallback = useSeatStore((s) => s.is2DFallback);

  const setCameraPreset = useSeatStore((s) => s.setCameraPreset);
  const toggle2DFallback = useSeatStore((s) => s.toggle2DFallback);
  const clearNotification = useSeatStore((s) => s.clearNotification);

  // Выбранные кресла и расчет итоговой стоимости
  const selectedSeats = useMemo(() => {
    return seats.filter((s) => selectedSeatIds.includes(s.id));
  }, [seats, selectedSeatIds]);

  const totalPrice = useMemo(() => {
    return selectedSeats.reduce((acc, s) => acc + s.price, 0);
  }, [selectedSeats]);

  const selectedSeatNumbers = useMemo(() => {
    return selectedSeats.map((s) => s.number).join(', ');
  }, [selectedSeats]);

  return (
    <div className={styles.uiOverlayRoot}>
      {/* Верхний брендовый бар и параметры ТС */}
      <div className={styles.topBar}>
        <div className={styles.vehicleInfo}>
          <div className={styles.carrierBadge}>{currentVehicle.carrierName}</div>
          <h2 className={styles.vehicleTitle}>{currentVehicle.name}</h2>
          <span className={styles.vehicleMeta}>
            Салон 2+1 · {currentVehicle.totalSeats} посадочных мест · Индивидуальный климат
          </span>
        </div>

        <div className={styles.topActions}>
          <button
            type="button"
            className={styles.modeSwitchBtn}
            onClick={toggle2DFallback}
            aria-label={is2DFallback ? 'Переключить в интерактивный 3D-режим' : 'Переключить в 2D-список мест'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <span>{is2DFallback ? '3D Панорама' : '2D Схема'}</span>
          </button>
        </div>
      </div>

      {/* Плавающая панель управления ракурсами камеры */}
      {!is2DFallback && (
        <div className={styles.cameraControlsHUD}>
          <div className={styles.hudLabel}>Ракурс камеры</div>
          <div className={styles.cameraBtnGroup}>
            {(
              [
                { id: 'hero', label: '3/4 Обзор' },
                { id: 'top', label: 'Сверху (План)' },
                { id: 'driver', label: 'От водителя' },
                { id: 'reset', label: 'Сброс' },
              ] as { id: CameraPreset; label: string }[]
            ).map((btn) => (
              <button
                key={btn.id}
                type="button"
                className={`${styles.cameraBtn} ${activePreset === btn.id ? styles.cameraBtnActive : ''}`}
                onClick={() => setCameraPreset(btn.id)}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Компактная легенда статусов в левом нижнем углу */}
      <div className={styles.legendCard}>
        <div className={styles.legendTitle}>Статусы мест</div>
        <div className={styles.legendGrid}>
          <div className={styles.legendItem}>
            <span className={`${styles.legendDot} ${styles.dotAvailable}`} />
            <span>Свободно</span>
          </div>
          <div className={styles.legendItem}>
            <span className={`${styles.legendDot} ${styles.dotSelected}`} />
            <span>Выбрано вами</span>
          </div>
          <div className={styles.legendItem}>
            <span className={`${styles.legendDot} ${styles.dotOccupied}`} />
            <span>Занято</span>
          </div>
          <div className={styles.legendItem}>
            <span className={`${styles.legendDot} ${styles.dotVip}`} />
            <span>Одиночное VIP</span>
          </div>
          <div className={styles.legendItem}>
            <span className={`${styles.legendDot} ${styles.dotDisabled}`} />
            <span>Для ОВЗ</span>
          </div>
          <div className={styles.legendItem}>
            <span className={`${styles.legendDot} ${styles.dotBlocked}`} />
            <span>Служебное</span>
          </div>
        </div>
      </div>

      {/* Всплывающее уведомление (лимиты, ошибки) */}
      {notification && (
        <div className={styles.toastNotification} role="alert">
          <div className={styles.toastText}>{notification}</div>
          <button type="button" className={styles.toastCloseBtn} onClick={clearNotification}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Нижняя фиксированная панель бронирования (Sticky Bar) */}
      <div className={styles.bottomStickyBar} aria-live="polite">
        <div className={styles.stickyBarContent}>
          <div className={styles.summaryBlock}>
            {selectedSeats.length === 0 ? (
              <div>
                <div className={styles.emptyPrompt}>Выберите место на 3D-схеме салона</div>
                <div className={styles.emptySubtext}>Нажмите на любое свободное кресло для просмотра деталей</div>
              </div>
            ) : (
              <div>
                <div className={styles.selectedCount}>
                  Выбрано {selectedSeats.length} {selectedSeats.length === 1 ? 'место' : 'места'}:{' '}
                  <span className={styles.seatNumbersHighlight}>{selectedSeatNumbers}</span>
                </div>
                <div className={styles.priceHighlight}>
                  Итого к оплате:{' '}
                  <span className={styles.priceValue}>{totalPrice.toLocaleString('ru-RU')} ₽</span>
                </div>
              </div>
            )}
          </div>

          <div className={styles.actionBlock}>
            <button
              type="button"
              className={styles.primaryCheckoutBtn}
              disabled={selectedSeats.length === 0}
              onClick={() => {
                alert(`Переход к оформлению: Места [${selectedSeatNumbers}], Сумма: ${totalPrice} ₽`);
              }}
            >
              <span>Продолжить</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
