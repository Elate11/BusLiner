import React, { Suspense, useState, useEffect } from 'react';
import { Scene } from './Scene';
import { UIOverlay } from './UIOverlay';
import { Fallback2D } from './Fallback2D';
import { useSeatStore } from './useSeatStore';
import styles from './SeatPicker3D.module.css';

// Надежная проверка поддержки WebGL в браузере
function checkWebGLSupport(): boolean {
  if (typeof window === 'undefined') return true;
  try {
    const canvas = document.createElement('canvas');
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch {
    return false;
  }
}

const LoadingPlaceholder: React.FC = () => (
  <div className={styles.loadingContainer}>
    <div className={styles.loadingCard}>
      <div className={styles.loadingSpinner} />
      <div className={styles.loadingTitle}>Загрузка 3D-модели салона...</div>
      <div className={styles.loadingSub}>Инициализация физических PBR-материалов и геометрии</div>
    </div>
  </div>
);

export const SeatPicker3D: React.FC = () => {
  const is2DFallback = useSeatStore((s) => s.is2DFallback);
  const [hasWebGL, setHasWebGL] = useState(true);

  useEffect(() => {
    setHasWebGL(checkWebGLSupport());
  }, []);

  return (
    <div className={styles.container}>
      {!hasWebGL || is2DFallback ? (
        <Fallback2D />
      ) : (
        <div className={styles.canvasWrapper}>
          <Suspense fallback={<LoadingPlaceholder />}>
            <Scene />
          </Suspense>
        </div>
      )}

      {/* Единый UI-оверлей управления и бронирования поверх Canvas */}
      <UIOverlay />
    </div>
  );
};
