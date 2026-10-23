import React, { useRef, useState, useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { useFrame, ThreeEvent } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { SeatData3D } from './types';
import { useSeatStore } from './useSeatStore';
import styles from './SeatPicker3D.module.css';

interface Seat3DProps {
  seat: SeatData3D;
  introDelay: number;
}

// ══════════════════════════════════════════════════════════════════════════════
// ПЕРЕИСПОЛЬЗУЕМЫЕ ПАРАМЕТРИЧЕСКИЕ 3D ГЕОМЕТРИИ ЛЮКСОВОГО КРЕСЛА SPRINTER COACH
// ══════════════════════════════════════════════════════════════════════════════
let sharedGeos: {
  cushionGeo: THREE.BufferGeometry;
  cushionInsertGeo: THREE.BufferGeometry;
  backrestGeo: THREE.BufferGeometry;
  backInsertGeo: THREE.BufferGeometry;
  headrestGeo: THREE.BufferGeometry;
  armrestGeo: THREE.BufferGeometry;
  trayGeo: THREE.BufferGeometry;
} | null = null;

function getSharedSeatGeometries() {
  if (sharedGeos) return sharedGeos;

  // 1. Анатомическая 3D подушка сиденья с боковыми валиками и водопадным краем
  const NX = 18, NZ = 18;
  const cVerts: number[] = [];
  const cIndices: number[] = [];

  for (let i = 0; i <= NX; i++) {
    const v = (i / NX) * 2 - 1; // -1 (зад) .. +1 (перед) по Z
    const z = v * 0.22;
    for (let j = 0; j <= NZ; j++) {
      const u = (j / NZ) * 2 - 1; // -1 (лево) .. +1 (право) по X
      const x = u * 0.21;

      let y = 0.095;
      // Боковые валики поддержки бёдер
      y += 0.042 * Math.pow(Math.abs(u), 2.2);
      // Анатомическое углубление в центре
      y += -0.015 * Math.cos(u * Math.PI * 0.5) * Math.cos(v * Math.PI * 0.5);
      // Водопадный завал спереди для комфорта подколенных сухожилий
      if (v > 0.35) {
        const t = (v - 0.35) / 0.65;
        y -= 0.075 * t * t * (3 - 2 * t);
      }
      if (v < -0.6) {
        y -= 0.025 * Math.pow((-v - 0.6) / 0.4, 2);
      }
      cVerts.push(x, y, z);
    }
  }

  const cStride = NZ + 1;
  for (let i = 0; i < NX; i++) {
    for (let j = 0; j < NZ; j++) {
      const a = i * cStride + j;
      const b = (i + 1) * cStride + j;
      const c = (i + 1) * cStride + (j + 1);
      const d = i * cStride + (j + 1);
      cIndices.push(a, b, d);
      cIndices.push(b, c, d);
    }
  }

  // Боковая юбка подушки
  const cTopCount = cVerts.length / 3;
  const cPerim: number[] = [];
  for (let j = 0; j <= NZ; j++) cPerim.push(NX * cStride + j);
  for (let i = NX - 1; i >= 0; i--) cPerim.push(i * cStride + NZ);
  for (let j = NZ - 1; j >= 0; j--) cPerim.push(0 * cStride + j);
  for (let i = 1; i < NX; i++) cPerim.push(i * cStride + 0);

  const cP = cPerim.length;
  for (let k = 0; k < cP; k++) {
    const topIdx = cPerim[k];
    cVerts.push(cVerts[topIdx * 3], 0.0, cVerts[topIdx * 3 + 2]);
  }
  for (let k = 0; k < cP; k++) {
    const nextK = (k + 1) % cP;
    const t0 = cPerim[k], t1 = cPerim[nextK];
    const b0 = cTopCount + k, b1 = cTopCount + nextK;
    cIndices.push(t0, b0, t1);
    cIndices.push(t1, b0, b1);
  }

  const cushionGeo = new THREE.BufferGeometry();
  cushionGeo.setAttribute('position', new THREE.Float32BufferAttribute(cVerts, 3));
  cushionGeo.setIndex(cIndices);
  cushionGeo.computeVertexNormals();

  // Центральная ребристая перфорированная вставка сиденья
  const ciVerts: number[] = [];
  const ciIndices: number[] = [];
  const ciNX = 14, ciNZ = 10;
  for (let i = 0; i <= ciNX; i++) {
    const v = (i / ciNX) * 2 - 1;
    const z = v * 0.19;
    for (let j = 0; j <= ciNZ; j++) {
      const u = (j / ciNZ) * 2 - 1;
      const x = u * 0.12;
      let y = 0.098;
      const ribs = 0.003 * Math.cos(u * Math.PI * 4);
      y += ribs - 0.012 * Math.cos(u * Math.PI * 0.5) * Math.cos(v * Math.PI * 0.5);
      if (v > 0.35) {
        const t = (v - 0.35) / 0.65;
        y -= 0.075 * t * t * (3 - 2 * t);
      }
      if (v < -0.6) {
        y -= 0.025 * Math.pow((-v - 0.6) / 0.4, 2);
      }
      ciVerts.push(x, y + 0.003, z);
    }
  }
  const ciStride = ciNZ + 1;
  for (let i = 0; i < ciNX; i++) {
    for (let j = 0; j < ciNZ; j++) {
      const a = i * ciStride + j;
      const b = (i + 1) * ciStride + j;
      const c = (i + 1) * ciStride + (j + 1);
      const d = i * ciStride + (j + 1);
      ciIndices.push(a, b, d);
      ciIndices.push(b, c, d);
    }
  }
  const cushionInsertGeo = new THREE.BufferGeometry();
  cushionInsertGeo.setAttribute('position', new THREE.Float32BufferAttribute(ciVerts, 3));
  cushionInsertGeo.setIndex(ciIndices);
  cushionInsertGeo.computeVertexNormals();

  // 2. Анатомическая 3D спинка сиденья с боковыми крыльями поддержки
  const bNY = 22, bNZ = 18;
  const bVerts: number[] = [];
  const bIndices: number[] = [];

  function bHalfW(v: number) {
    if (v < 0.28) return 0.195 + (0.175 - 0.195) * (v / 0.28);
    if (v < 0.75) return 0.175 + (0.225 - 0.175) * ((v - 0.28) / 0.47);
    return 0.225 + (0.185 - 0.225) * ((v - 0.75) / 0.25);
  }

  function bZCenter(v: number) {
    return 0.048 * Math.sin(v * Math.PI) - 0.02 * Math.pow(v, 2);
  }

  for (let i = 0; i <= bNY; i++) {
    const v = i / bNY;
    const y = v * 0.64;
    const w = bHalfW(v);
    const zc = bZCenter(v);

    for (let j = 0; j <= bNZ; j++) {
      const u = (j / bNZ) * 2 - 1;
      const x = u * w;
      // Боковые валики торса (+5.5 см вперед)
      const bolster = 0.055 * Math.pow(Math.abs(u), 2.2) * Math.sin(Math.min(1, v / 0.8) * Math.PI);
      const z = zc + bolster;
      bVerts.push(x, y, z);
    }
  }

  const bStride = bNZ + 1;
  for (let i = 0; i < bNY; i++) {
    for (let j = 0; j < bNZ; j++) {
      const a = i * bStride + j;
      const b = (i + 1) * bStride + j;
      const c = (i + 1) * bStride + (j + 1);
      const d = i * bStride + (j + 1);
      bIndices.push(a, b, d);
      bIndices.push(b, c, d);
    }
  }

  const bFrontCount = bVerts.length / 3;
  for (let i = 0; i <= bNY; i++) {
    const v = i / bNY;
    const y = v * 0.64;
    const w = bHalfW(v) * 0.95;
    const zc = bZCenter(v) - 0.065;

    for (let j = 0; j <= bNZ; j++) {
      const u = (j / bNZ) * 2 - 1;
      const x = u * w;
      bVerts.push(x, y, zc);
    }
  }

  for (let i = 0; i < bNY; i++) {
    for (let j = 0; j < bNZ; j++) {
      const a = bFrontCount + i * bStride + j;
      const b = bFrontCount + (i + 1) * bStride + j;
      const c = bFrontCount + (i + 1) * bStride + (j + 1);
      const d = bFrontCount + i * bStride + (j + 1);
      bIndices.push(a, d, b);
      bIndices.push(b, d, c);
    }
  }

  const bPerimF: number[] = [];
  const bPerimB: number[] = [];
  for (let j = 0; j <= bNZ; j++) {
    bPerimF.push(bNY * bStride + j);
    bPerimB.push(bFrontCount + bNY * bStride + j);
  }
  for (let i = bNY - 1; i >= 0; i--) {
    bPerimF.push(i * bStride + bNZ);
    bPerimB.push(bFrontCount + i * bStride + bNZ);
  }
  for (let j = bNZ - 1; j >= 0; j--) {
    bPerimF.push(0 * bStride + j);
    bPerimB.push(bFrontCount + 0 * bStride + j);
  }
  for (let i = 1; i < bNY; i++) {
    bPerimF.push(i * bStride + 0);
    bPerimB.push(bFrontCount + i * bStride + 0);
  }
  const bP = bPerimF.length;
  for (let k = 0; k < bP; k++) {
    const nextK = (k + 1) % bP;
    bIndices.push(bPerimF[k], bPerimB[k], bPerimF[nextK]);
    bIndices.push(bPerimF[nextK], bPerimB[k], bPerimB[nextK]);
  }

  const backrestGeo = new THREE.BufferGeometry();
  backrestGeo.setAttribute('position', new THREE.Float32BufferAttribute(bVerts, 3));
  backrestGeo.setIndex(bIndices);
  backrestGeo.computeVertexNormals();

  // Центральная вставка спинки
  const biVerts: number[] = [];
  const biIndices: number[] = [];
  const biNY = 18, biNZ = 10;
  for (let i = 0; i <= biNY; i++) {
    const v = i / biNY;
    const y = 0.04 + v * 0.56;
    const zc = bZCenter(v);
    for (let j = 0; j <= biNZ; j++) {
      const u = (j / biNZ) * 2 - 1;
      const x = u * 0.11;
      const ribs = 0.0035 * Math.cos(u * Math.PI * 4);
      const z = zc + 0.004 + ribs;
      biVerts.push(x, y, z);
    }
  }
  const biStride = biNZ + 1;
  for (let i = 0; i < biNY; i++) {
    for (let j = 0; j < biNZ; j++) {
      const a = i * biStride + j;
      const b = (i + 1) * biStride + j;
      const c = (i + 1) * biStride + (j + 1);
      const d = i * biStride + (j + 1);
      biIndices.push(a, b, d);
      biIndices.push(b, c, d);
    }
  }
  const backInsertGeo = new THREE.BufferGeometry();
  backInsertGeo.setAttribute('position', new THREE.Float32BufferAttribute(biVerts, 3));
  backInsertGeo.setIndex(biIndices);
  backInsertGeo.computeVertexNormals();

  // 3. Анатомический подушечный подголовник с боковыми ушками
  const hNY = 12, hNZ = 16;
  const hVerts: number[] = [];
  const hIndices: number[] = [];

  for (let i = 0; i <= hNY; i++) {
    const v = (i / hNY) * 2 - 1;
    const y = v * 0.09;
    for (let j = 0; j <= hNZ; j++) {
      const u = (j / hNZ) * 2 - 1;
      const x = u * 0.14;
      const earWings = 0.032 * Math.pow(Math.abs(u), 1.8);
      const pillow = 0.02 * Math.cos(u * Math.PI * 0.5) * Math.cos(v * Math.PI * 0.5);
      const z = pillow + earWings;
      hVerts.push(x, y, z);
    }
  }
  const hStride = hNZ + 1;
  for (let i = 0; i < hNY; i++) {
    for (let j = 0; j < hNZ; j++) {
      const a = i * hStride + j;
      const b = (i + 1) * hStride + j;
      const c = (i + 1) * hStride + (j + 1);
      const d = i * hStride + (j + 1);
      hIndices.push(a, b, d);
      hIndices.push(b, c, d);
    }
  }
  const hFrontCount = hVerts.length / 3;
  for (let i = 0; i <= hNY; i++) {
    const v = (i / hNY) * 2 - 1;
    const y = v * 0.09;
    for (let j = 0; j <= hNZ; j++) {
      const u = (j / hNZ) * 2 - 1;
      const x = u * 0.135;
      hVerts.push(x, y, -0.065);
    }
  }
  for (let i = 0; i < hNY; i++) {
    for (let j = 0; j < hNZ; j++) {
      const a = hFrontCount + i * hStride + j;
      const b = hFrontCount + (i + 1) * hStride + j;
      const c = hFrontCount + (i + 1) * hStride + (j + 1);
      const d = hFrontCount + i * hStride + (j + 1);
      hIndices.push(a, d, b);
      hIndices.push(b, d, c);
    }
  }
  const hPerimF: number[] = [];
  const hPerimB: number[] = [];
  for (let j = 0; j <= hNZ; j++) {
    hPerimF.push(hNY * hStride + j);
    hPerimB.push(hFrontCount + hNY * hStride + j);
  }
  for (let i = hNY - 1; i >= 0; i--) {
    hPerimF.push(i * hStride + hNZ);
    hPerimB.push(hFrontCount + i * hStride + hNZ);
  }
  for (let j = hNZ - 1; j >= 0; j--) {
    hPerimF.push(0 * hStride + j);
    hPerimB.push(hFrontCount + 0 * hStride + j);
  }
  for (let i = 1; i < hNY; i++) {
    hPerimF.push(i * hStride + 0);
    hPerimB.push(hFrontCount + i * hStride + 0);
  }
  const hP = hPerimF.length;
  for (let k = 0; k < hP; k++) {
    const nextK = (k + 1) % hP;
    hIndices.push(hPerimF[k], hPerimB[k], hPerimF[nextK]);
    hIndices.push(hPerimF[nextK], hPerimB[k], hPerimB[nextK]);
  }
  const headrestGeo = new THREE.BufferGeometry();
  headrestGeo.setAttribute('position', new THREE.Float32BufferAttribute(hVerts, 3));
  headrestGeo.setIndex(hIndices);
  headrestGeo.computeVertexNormals();

  // 4. Скругленный эргономичный подлокотник
  const aShape = new THREE.Shape();
  aShape.moveTo(-0.15, 0.028);
  aShape.lineTo(0.12, 0.028);
  aShape.quadraticCurveTo(0.17, 0.024, 0.16, -0.022);
  aShape.quadraticCurveTo(0.14, -0.034, 0.11, -0.034);
  aShape.lineTo(-0.14, -0.034);
  aShape.quadraticCurveTo(-0.165, -0.012, -0.15, 0.028);

  const armrestGeo = new THREE.ExtrudeGeometry(aShape, {
    depth: 0.046,
    bevelEnabled: true,
    bevelThickness: 0.012,
    bevelSize: 0.012,
    bevelSegments: 4,
    curveSegments: 14,
  });
  armrestGeo.translate(0, 0, -0.023);

  // Складной столик
  const trayShape = new THREE.Shape();
  trayShape.moveTo(-0.012, -0.13);
  trayShape.lineTo(0.012, -0.13);
  trayShape.quadraticCurveTo(0.018, -0.13, 0.018, -0.12);
  trayShape.lineTo(0.018, 0.12);
  trayShape.quadraticCurveTo(0.018, 0.13, 0.012, 0.13);
  trayShape.lineTo(-0.012, 0.13);
  trayShape.quadraticCurveTo(-0.018, 0.13, -0.018, 0.12);
  trayShape.lineTo(-0.018, -0.12);
  trayShape.quadraticCurveTo(-0.018, -0.13, -0.012, -0.13);

  const trayGeo = new THREE.ExtrudeGeometry(trayShape, {
    depth: 0.28,
    bevelEnabled: true,
    bevelThickness: 0.008,
    bevelSize: 0.008,
    bevelSegments: 3,
    curveSegments: 10,
  });
  trayGeo.translate(0, 0, -0.14);

  sharedGeos = {
    cushionGeo,
    cushionInsertGeo,
    backrestGeo,
    backInsertGeo,
    headrestGeo,
    armrestGeo,
    trayGeo,
  };
  return sharedGeos;
}

// Общие PBR-материалы фурнитуры
const chromeMetalMaterial = new THREE.MeshStandardMaterial({
  color: '#F1F5F9',
  metalness: 0.98,
  roughness: 0.12,
});

const darkPlasticMaterial = new THREE.MeshStandardMaterial({
  color: '#0F172A',
  metalness: 0.15,
  roughness: 0.72,
});

const redButtonMaterial = new THREE.MeshStandardMaterial({
  color: '#DC2626',
  roughness: 0.4,
});

export const Seat3D: React.FC<Seat3DProps> = ({ seat, introDelay }) => {
  const groupRef = useRef<THREE.Group>(null);
  const [isHoveredLocal, setIsHoveredLocal] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const hoverTimerRef = useRef<NodeJS.Timeout | null>(null);

  const selectedSeatIds = useSeatStore((s) => s.selectedSeatIds);
  const selectedRow = useSeatStore((s) => s.selectedRow);
  const isIntroActive = useSeatStore((s) => s.isIntroActive);
  const toggleSeat = useSeatStore((s) => s.toggleSeat);
  const setHoveredSeat = useSeatStore((s) => s.setHoveredSeat);

  const isSelected = selectedSeatIds.includes(seat.id);
  const isOccupied = seat.status === 'occupied';
  const isBlocked = seat.status === 'blocked';
  const isDisabled = seat.status === 'disabled';
  const isAvailable = seat.status === 'available';

  const isDimmed = selectedRow !== null && seat.row !== selectedRow && !isSelected;

  const geos = useMemo(() => getSharedSeatGeometries(), []);

  // Цвет кожаной обивки
  const upholsteryColor = useMemo(() => {
    if (isSelected) return '#1E3A8A'; // Фирменный deep navy
    if (isBlocked) return '#94A3B8';
    if (isOccupied) return '#64748B';
    if (isDisabled) return '#1D4ED8';
    if (seat.category === 'vip' || seat.category === 'panoramic') return '#0F172A';
    if (seat.category === 'emergency_exit' || seat.category === 'extra_legroom') return '#0369A1';
    if (seat.category === 'limited_recline') return '#475569';
    return '#1E293B';
  }, [isSelected, isBlocked, isOccupied, isDisabled, seat.category]);

  const insertColor = useMemo(() => {
    if (isSelected) return '#2563EB';
    if (isBlocked) return '#CBD5E1';
    if (isOccupied) return '#94A3B8';
    if (isDisabled) return '#3B82F6';
    if (seat.category === 'vip' || seat.category === 'panoramic') return '#1E3A8A';
    if (seat.category === 'emergency_exit' || seat.category === 'extra_legroom') return '#0284C7';
    if (seat.category === 'limited_recline') return '#64748B';
    return '#334155';
  }, [isSelected, isBlocked, isOccupied, isDisabled, seat.category]);

  // Высококлассная кожа Nappa
  const leatherMaterial = useMemo(() => {
    return new THREE.MeshPhysicalMaterial({
      color: upholsteryColor,
      roughness: 0.38,
      metalness: 0.05,
      clearcoat: isSelected ? 0.35 : 0.15,
      clearcoatRoughness: 0.25,
      transparent: true,
      opacity: isDimmed ? 0.35 : 1.0,
    });
  }, [upholsteryColor, isSelected, isDimmed]);

  // Перфорированная центральная секция
  const insertMaterial = useMemo(() => {
    return new THREE.MeshPhysicalMaterial({
      color: insertColor,
      roughness: 0.65,
      metalness: 0.02,
      clearcoat: 0.08,
      transparent: true,
      opacity: isDimmed ? 0.35 : 1.0,
    });
  }, [insertColor, isDimmed]);

  // Текстура номера места для таблички
  const numberTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = isSelected ? '#1E3A8A' : '#0F172A';
      ctx.fillRect(0, 0, 128, 128);
      ctx.strokeStyle = isSelected ? '#93C5FD' : '#FFFFFF';
      ctx.lineWidth = 6;
      ctx.strokeRect(6, 6, 116, 116);
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '800 68px "Plus Jakarta Sans", sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(seat.number, 64, 64);
    }
    const tex = new THREE.CanvasTexture(canvas);
    return tex;
  }, [seat.number, isSelected]);

  useEffect(() => {
    if (isHoveredLocal && isAvailable) {
      hoverTimerRef.current = setTimeout(() => {
        setShowTooltip(true);
      }, 120);
    } else {
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
      setShowTooltip(false);
    }
    return () => {
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    };
  }, [isHoveredLocal, isAvailable]);

  useFrame((state, delta) => {
    if (!groupRef.current) return;

    if (isIntroActive) {
      const elapsed = state.clock.getElapsedTime();
      const delay = (seat.row * 0.15) + introDelay;
      if (elapsed < delay) {
        groupRef.current.position.y = -0.5;
        groupRef.current.scale.set(0.01, 0.01, 0.01);
        return;
      }
    }

    groupRef.current.scale.damp(new THREE.Vector3(1, 1, 1), 6, delta);

    const targetY = isSelected ? 0.035 : isHoveredLocal && isAvailable ? 0.012 : 0;
    groupRef.current.position.y = THREE.MathUtils.damp(
      groupRef.current.position.y,
      seat.position[1] + targetY,
      10,
      delta
    );
  });

  const handlePointerOver = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    setIsHoveredLocal(true);
    setHoveredSeat(seat);
    document.body.style.cursor = isAvailable ? 'pointer' : 'not-allowed';
  };

  const handlePointerOut = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    setIsHoveredLocal(false);
    setHoveredSeat(null);
    document.body.style.cursor = 'default';
  };

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    if (isAvailable) {
      toggleSeat(seat.id);
    }
  };

  const aisleX = seat.col === 3 ? -0.21 : 0.21;

  return (
    <group
      ref={groupRef}
      position={[seat.position[0], seat.position[1], seat.position[2]]}
      rotation={[0, seat.rotationY || 0, 0]}
      onClick={handleClick}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
      dispose={null}
    >
      {/* ── 1. СТАЛЬНЫЕ ОПОРЫ И КРЕПЛЕНИЯ К ПОЛУ ── */}
      {[-0.14, 0.14].map((lx, idx) => (
        <group key={`leg-${idx}`}>
          <mesh material={chromeMetalMaterial} position={[lx, 0.14, 0.09]} castShadow>
            <cylinderGeometry args={[0.015, 0.015, 0.28, 16]} />
          </mesh>
          <mesh material={chromeMetalMaterial} position={[lx, 0.14, -0.13]} castShadow>
            <cylinderGeometry args={[0.015, 0.015, 0.28, 16]} />
          </mesh>
          <mesh material={chromeMetalMaterial} position={[lx, 0.013, -0.02]}>
            <boxGeometry args={[0.046, 0.026, 0.28]} />
          </mesh>
          <mesh material={chromeMetalMaterial} position={[lx, 0.03, -0.09]}>
            <cylinderGeometry args={[0.007, 0.007, 0.012, 6]} />
          </mesh>
          <mesh material={chromeMetalMaterial} position={[lx, 0.03, 0.06]}>
            <cylinderGeometry args={[0.007, 0.007, 0.012, 6]} />
          </mesh>
        </group>
      ))}

      {/* Подножка для заднего пассажира */}
      <mesh material={chromeMetalMaterial} position={[0, 0.10, -0.16]}>
        <cylinderGeometry args={[0.01, 0.01, 0.36, 16]} />
      </mesh>

      {/* Нижний пластиковый кожух основания */}
      <mesh material={darkPlasticMaterial} position={[0, 0.26, 0]} castShadow>
        <boxGeometry args={[0.40, 0.06, 0.38]} />
      </mesh>

      {/* Рычаг наклона спинки */}
      <mesh
        material={chromeMetalMaterial}
        position={[aisleX, 0.26, 0.05]}
        rotation={[0, seat.col === 3 ? 0.2 : -0.2, 0]}
      >
        <boxGeometry args={[0.025, 0.016, 0.07]} />
      </mesh>

      {/* Замок ремня безопасности с ярко-красной кнопкой */}
      <group position={[-aisleX * 0.95, 0.32, 0.02]}>
        <mesh material={darkPlasticMaterial}>
          <boxGeometry args={[0.012, 0.10, 0.018]} />
        </mesh>
        <mesh material={darkPlasticMaterial} position={[0, 0.05, 0]}>
          <boxGeometry args={[0.035, 0.045, 0.026]} />
        </mesh>
        <mesh material={redButtonMaterial} position={[0, 0.075, 0]}>
          <boxGeometry args={[0.026, 0.014, 0.012]} />
        </mesh>
      </group>

      {/* ── 2. АНАТОМИЧЕСКАЯ ПОДУШКА СИДЕНЬЯ ── */}
      <group position={[0, 0.28, 0]}>
        <mesh geometry={geos.cushionGeo} material={leatherMaterial} castShadow receiveShadow />
        <mesh geometry={geos.cushionInsertGeo} material={insertMaterial} />
      </group>

      {/* ── 3. АНАТОМИЧЕСКАЯ СПИНКА С БОКОВОЙ ПОДДЕРЖКОЙ ── */}
      <group position={[0, 0.36, -0.16]} rotation={[-0.14, 0, 0]}>
        <mesh geometry={geos.backrestGeo} material={leatherMaterial} castShadow receiveShadow />
        <mesh geometry={geos.backInsertGeo} material={insertMaterial} />

        {/* Складной столик на спинке */}
        <mesh geometry={geos.trayGeo} material={darkPlasticMaterial} position={[0, 0.34, -0.078]} />

        {/* Двойные подстаканники */}
        {[-0.065, 0.065].map((cx, i) => (
          <mesh
            key={`cup-${i}`}
            material={chromeMetalMaterial}
            position={[cx, 0.34, -0.088]}
            rotation={[0, 0, 0]}
          >
            <torusGeometry args={[0.032, 0.0035, 8, 24]} />
          </mesh>
        ))}

        {/* Защелка столика */}
        <mesh material={chromeMetalMaterial} position={[0, 0.47, -0.082]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.008, 0.008, 0.02, 12]} />
        </mesh>

        {/* Сетка для журналов */}
        <mesh material={darkPlasticMaterial} position={[0, 0.15, -0.076]}>
          <boxGeometry args={[0.30, 0.16, 0.012]} />
        </mesh>

        {/* Верхний поручень спинки */}
        <mesh material={chromeMetalMaterial} position={[0, 0.64, -0.04]} rotation={[0, 0, 0]}>
          <torusGeometry args={[0.065, 0.009, 12, 28, Math.PI]} />
        </mesh>

        {/* Стойки подголовника */}
        {[-0.055, 0.055].map((hx, i) => (
          <group key={`post-${i}`}>
            <mesh material={chromeMetalMaterial} position={[hx, 0.66, -0.015]}>
              <cylinderGeometry args={[0.0065, 0.0065, 0.12, 16]} />
            </mesh>
            <mesh material={chromeMetalMaterial} position={[hx, 0.63, -0.015]}>
              <cylinderGeometry args={[0.012, 0.012, 0.01, 16]} />
            </mesh>
          </group>
        ))}

        {/* Анатомический подголовник */}
        <mesh geometry={geos.headrestGeo} material={leatherMaterial} position={[0, 0.73, -0.005]} castShadow />

        {/* Номер места на подголовнике */}
        <mesh position={[0, 0.73, 0.038]}>
          <planeGeometry args={[0.13, 0.10]} />
          <meshBasicMaterial map={numberTexture} />
        </mesh>
      </group>

      {/* ── 4. ПОДЛОКОТНИК СО СТОРОНЫ ПРОХОДА ── */}
      <group position={[aisleX, 0.52, 0.04]} rotation={[0, Math.PI / 2, 0]}>
        <mesh geometry={geos.armrestGeo} material={darkPlasticMaterial} castShadow />
        <mesh material={leatherMaterial} position={[0.01, 0.034, 0]}>
          <boxGeometry args={[0.24, 0.012, 0.044]} />
        </mesh>
        <mesh material={chromeMetalMaterial} position={[-0.14, -0.005, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.02, 0.02, 0.048, 20]} />
        </mesh>
        <mesh material={chromeMetalMaterial} position={[0.14, -0.012, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.008, 0.008, 0.05, 14]} />
        </mesh>
      </group>

      {/* ── 5. HTML TOOLTIP НАД ПОДГОЛОВНИКОМ ── */}
      {showTooltip && (
        <Html
          position={[0, 1.25, -0.15]}
          center
          distanceFactor={6.5}
          zIndexRange={[100, 0]}
          style={{ pointerEvents: 'none' }}
        >
          <div className={styles.seatTooltip}>
            <div className={styles.tooltipHeader}>
              <span className={styles.tooltipNumber}>Место {seat.number}</span>
              <span className={styles.tooltipPrice}>{seat.price} ₽</span>
            </div>
            <div className={styles.tooltipCategory}>
              {seat.category === 'vip' && 'VIP (Одиночное место)'}
              {seat.category === 'window' && 'Место у окна'}
              {seat.category === 'aisle' && 'Место у прохода'}
              {seat.category === 'emergency_exit' && 'Аварийный выход (+12 см)'}
              {seat.category === 'extra_legroom' && 'Дополнительное место для ног'}
              {seat.category === 'family' && 'Семейная зона (ISOFIX)'}
              {seat.category === 'limited_recline' && 'Неоткидная спинка'}
              {seat.category === 'panoramic' && 'Панорамный обзор'}
            </div>
            {seat.features && seat.features.length > 0 && (
              <ul className={styles.tooltipFeatures}>
                {seat.features.map((feat, idx) => (
                  <li key={idx}>{feat}</li>
                ))}
              </ul>
            )}
          </div>
        </Html>
      )}
    </group>
  );
};
