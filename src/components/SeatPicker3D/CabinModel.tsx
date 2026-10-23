import React, { useMemo } from 'react';
import * as THREE from 'three';
import { VehicleConfig3D } from './types';

// Общие материалы кузова и интерьера для исключения дублирования
const floorMaterial = new THREE.MeshStandardMaterial({
  color: '#CBD5E1',
  roughness: 0.9,
  metalness: 0.1,
});

const runnerMaterial = new THREE.MeshStandardMaterial({
  color: '#64748B',
  roughness: 0.95,
  metalness: 0.05,
});

const glassMaterial = new THREE.MeshPhysicalMaterial({
  color: '#BAE6FD',
  transmission: 0.98,
  opacity: 0.12,
  transparent: true,
  roughness: 0.02,
  ior: 1.5,
  depthWrite: false,
});

const rubberTrimMaterial = new THREE.MeshStandardMaterial({
  color: '#0F172A',
  roughness: 0.8,
  metalness: 0.1,
});

const railMaterial = new THREE.MeshStandardMaterial({
  color: '#F59E0B', // Индустриальный сигнальный желтый для безопасности
  metalness: 0.65,
  roughness: 0.35,
});

const dashMaterial = new THREE.MeshStandardMaterial({
  color: '#1E293B',
  roughness: 0.5,
  metalness: 0.2,
});

const ceilingTrimMaterial = new THREE.MeshPhysicalMaterial({
  color: '#F8FAFC',
  roughness: 0.2,
  metalness: 0.05,
  transparent: true,
  opacity: 0.38, // полупрозрачные стенки
  transmission: 0.6,
  depthWrite: false,
  side: THREE.DoubleSide,
});

const ledLightMaterial = new THREE.MeshStandardMaterial({
  color: '#FFFFFF',
  emissive: '#FEF08A',
  emissiveIntensity: 0.4,
});

export const CabinModel: React.FC<{ vehicle: VehicleConfig3D }> = ({ vehicle }) => {
  const { length, width } = vehicle.dimensions;
  const halfLen = length / 2;

  // Оконные стойки (боковые пилоны между стеклопакетами)
  const pillarPositions = useMemo(() => {
    return [1.8, 0.7, -0.4, -1.5, -2.6];
  }, []);

  return (
    <group dispose={null}>
      {/* 1. Основание кузова и многослойный пол */}
      <mesh material={floorMaterial} position={[0, -0.06, 0]} receiveShadow>
        <boxGeometry args={[width + 0.1, 0.12, length]} />
      </mesh>

      {/* 2. Антискользящая текстурированная ковровая дорожка прохода */}
      <mesh material={runnerMaterial} position={[0.08, 0.002, 0]} receiveShadow>
        <planeGeometry args={[0.52, length - 1.2]} />
      </mesh>

      {/* 3. Направляющие рельсы фиксации кресел в полу (алюминиевый профиль) */}
      <mesh position={[-0.47, 0.003, 0]} receiveShadow>
        <boxGeometry args={[0.04, 0.005, length - 1.5]} />
        <meshStandardMaterial color="#94A3B8" metalness={0.8} roughness={0.3} />
      </mesh>
      <mesh position={[0.58, 0.003, 0]} receiveShadow>
        <boxGeometry args={[0.04, 0.005, length - 1.5]} />
        <meshStandardMaterial color="#94A3B8" metalness={0.8} roughness={0.3} />
      </mesh>

      {/* 4. Панорамные боковые окна с двойным остеклением и уплотнителями */}
      {/* Левая сторона */}
      <mesh material={glassMaterial} position={[-width / 2, 0.85, 0]}>
        <boxGeometry args={[0.02, 0.78, length - 1.2]} />
      </mesh>
      {/* Резиновый уплотнитель окна */}
      <mesh material={rubberTrimMaterial} position={[-width / 2 + 0.01, 0.46, 0]}>
        <boxGeometry args={[0.025, 0.02, length - 1.18]} />
      </mesh>
      <mesh material={rubberTrimMaterial} position={[-width / 2 + 0.01, 1.24, 0]}>
        <boxGeometry args={[0.025, 0.02, length - 1.18]} />
      </mesh>

      {/* Правая сторона */}
      <mesh material={glassMaterial} position={[width / 2, 0.85, -0.6]}>
        <boxGeometry args={[0.02, 0.78, length - 2.4]} />
      </mesh>
      <mesh material={rubberTrimMaterial} position={[width / 2 - 0.01, 0.46, -0.6]}>
        <boxGeometry args={[0.025, 0.02, length - 2.38]} />
      </mesh>
      <mesh material={rubberTrimMaterial} position={[width / 2 - 0.01, 1.24, -0.6]}>
        <boxGeometry args={[0.025, 0.02, length - 2.38]} />
      </mesh>

      {/* 5. Конструкционные пилоны (стойки кузова) между окнами */}
      {pillarPositions.map((posZ, idx) => (
        <group key={`pillar-${idx}`}>
          <mesh material={ceilingTrimMaterial} position={[-width / 2 + 0.02, 0.85, posZ]} castShadow>
            <boxGeometry args={[0.06, 0.82, 0.12]} />
          </mesh>
          {idx > 0 && (
            <mesh material={ceilingTrimMaterial} position={[width / 2 - 0.02, 0.85, posZ]} castShadow>
              <boxGeometry args={[0.06, 0.82, 0.12]} />
            </mesh>
          )}
        </group>
      ))}

      {/* 6. Потолочный свод со встроенными светильниками и дефлекторами кондиционера */}
      <mesh material={ceilingTrimMaterial} position={[0, 1.82, 0]}>
        <boxGeometry args={[width, 0.06, length - 0.8]} />
      </mesh>
      {/* Светодиодные плафоны освещения салона */}
      <mesh material={ledLightMaterial} position={[-0.35, 1.78, 0]}>
        <boxGeometry args={[0.06, 0.01, length - 2.0]} />
      </mesh>
      <mesh material={ledLightMaterial} position={[0.35, 1.78, 0]}>
        <boxGeometry args={[0.06, 0.01, length - 2.0]} />
      </mesh>

      {/* 7. Входная группа: ступень с контрастным противоскользящим кантом */}
      <group position={[width / 2 - 0.15, -0.05, 1.95]}>
        <mesh position={[0, -0.1, 0]} receiveShadow>
          <boxGeometry args={[0.45, 0.12, 0.85]} />
          <meshStandardMaterial color="#334155" roughness={0.8} />
        </mesh>
        {/* Контрастный сигнальный кант ступени */}
        <mesh position={[0.22, -0.03, 0]}>
          <boxGeometry args={[0.03, 0.02, 0.85]} />
          <meshStandardMaterial color="#FACC15" roughness={0.4} />
        </mesh>
      </group>

      {/* 8. Поручни безопасности при посадке и в проходе (желтое порошковое покрытие) */}
      <group position={[0.42, 0.85, 1.5]}>
        {/* Вертикальная стойка */}
        <mesh material={railMaterial} castShadow>
          <cylinderGeometry args={[0.016, 0.016, 1.8, 16]} />
        </mesh>
        {/* Верхний фланец крепления к потолку */}
        <mesh position={[0, 0.89, 0]}>
          <cylinderGeometry args={[0.03, 0.03, 0.02, 16]} />
          <meshStandardMaterial color="#0F172A" metalness={0.7} />
        </mesh>
      </group>

      {/* 9. Кокпит водителя Mercedes-Benz Sprinter */}
      <group position={[0, 0, halfLen - 0.8]}>
        {/* Приборная панель и торпедо */}
        <mesh material={dashMaterial} position={[-0.45, 0.5, 0]} castShadow>
          <boxGeometry args={[0.85, 0.65, 0.75]} />
        </mesh>
        {/* Цифровая приборная панель MBUX */}
        <mesh position={[-0.45, 0.74, 0.1]} rotation={[0.35, 0, 0]}>
          <boxGeometry args={[0.42, 0.15, 0.02]} />
          <meshStandardMaterial color="#0284C7" emissive="#0369A1" emissiveIntensity={0.5} />
        </mesh>
        {/* Рулевая колонка и мультируль */}
        <mesh position={[-0.45, 0.62, 0.15]} rotation={[0.45, 0, 0]}>
          <cylinderGeometry args={[0.022, 0.022, 0.28, 16]} />
          <meshStandardMaterial color="#0F172A" metalness={0.6} />
        </mesh>
        <mesh position={[-0.45, 0.78, 0.26]} rotation={[0.45, 0, 0]} castShadow>
          <torusGeometry args={[0.18, 0.018, 16, 32]} />
          <meshStandardMaterial color="#1E293B" roughness={0.4} metalness={0.3} />
        </mesh>

        {/* Кресло водителя со специализированной подвеской */}
        <group position={[-0.45, 0.0, -0.45]}>
          <mesh position={[0, 0.35, 0]} castShadow>
            <boxGeometry args={[0.48, 0.12, 0.48]} />
            <meshStandardMaterial color="#0F172A" roughness={0.7} />
          </mesh>
          <mesh position={[0, 0.72, -0.2]} rotation={[0.08, 0, 0]} castShadow>
            <boxGeometry args={[0.46, 0.65, 0.1]} />
            <meshStandardMaterial color="#0F172A" roughness={0.7} />
          </mesh>
        </group>

        {/* Защитный барьер за водителем из прозрачного поликарбоната */}
        <mesh position={[-0.45, 0.8, -0.75]}>
          <boxGeometry args={[0.85, 0.9, 0.015]} />
          <meshPhysicalMaterial color="#E2E8F0" transmission={0.92} opacity={0.3} transparent roughness={0.1} />
        </mesh>
      </group>

      {/* 10. Задняя стенка и багажный отсек */}
      <mesh position={[0, 0.9, -halfLen + 0.3]} castShadow>
        <boxGeometry args={[width + 0.05, 1.8, 0.1]} />
        <meshStandardMaterial color="#475569" roughness={0.8} />
      </mesh>
    </group>
  );
};
