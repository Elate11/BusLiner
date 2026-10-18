import React from 'react';
import styles from './SeatPicker.module.css';

export const Legend: React.FC = () => {
  return (
    <nav className={styles.legend} aria-label="Обозначения мест на схеме">
      <div className={styles.legendItem}>
        <span className={`${styles.legendChip} ${styles.legendChip_available}`} />
        <span className={styles.legendText}>Свободно</span>
      </div>

      <div className={styles.legendItem}>
        <span className={`${styles.legendChip} ${styles.legendChip_selected}`} />
        <span className={styles.legendText}>Выбрано вами</span>
      </div>

      <div className={styles.legendItem}>
        <span className={`${styles.legendChip} ${styles.legendChip_occupied}`} />
        <span className={styles.legendText}>Занято</span>
      </div>

      <div className={styles.legendItem}>
        <span className={`${styles.legendChip} ${styles.legendChip_blocked}`} />
        <span className={styles.legendText}>Недоступно</span>
      </div>

      <div className={styles.legendItem}>
        <span className={`${styles.legendChip} ${styles.legendChip_female}`} />
        <span className={styles.legendText}>Только женщины</span>
      </div>

      <div className={styles.legendItem}>
        <span className={`${styles.legendChip} ${styles.legendChip_male}`} />
        <span className={styles.legendText}>Только мужчины</span>
      </div>

      <div className={styles.legendItem}>
        <span className={`${styles.legendChip} ${styles.legendChip_disabled}`} />
        <span className={styles.legendText}>Для пассажиров с ОВЗ</span>
      </div>
    </nav>
  );
};
