import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { useSeatStore } from './useSeatStore';
import { CabinModel } from './CabinModel';
import { Seat3D } from './Seat3D';

const CameraController: React.FC = () => {
  const { camera } = useThree();
  const controlsRef = useRef<OrbitControlsImpl>(null);

  const targetPos = useSeatStore((s) => s.cameraTargetPos);
  const lookAt = useSeatStore((s) => s.cameraLookAt);
  const isIntroActive = useSeatStore((s) => s.isIntroActive);
  const skipIntro = useSeatStore((s) => s.skipIntro);

  const desiredPos = useRef(new THREE.Vector3(...targetPos));
  const desiredLook = useRef(new THREE.Vector3(...lookAt));

  useEffect(() => {
    desiredPos.current.set(...targetPos);
    desiredLook.current.set(...lookAt);
  }, [targetPos, lookAt]);

  // Кинематографичный стартовый пролет: камера стартует с дальней точки
  useEffect(() => {
    if (isIntroActive) {
      camera.position.set(8.5, 6.0, 7.5);
      const timer = setTimeout(() => {
        skipIntro();
      }, 1800);
      return () => clearTimeout(timer);
    }
  }, []);

  useFrame((_, delta) => {
    // Плавная интерполяция позиции камеры и центра вращения
    camera.position.damp(desiredPos.current, isIntroActive ? 2.5 : 4.5, delta);

    if (controlsRef.current) {
      controlsRef.current.target.damp(desiredLook.current, 5, delta);
      controlsRef.current.update();
    }
  });

  return (
    <OrbitControls
      ref={controlsRef}
      enablePan={false}
      enableDamping
      dampingFactor={0.06}
      minDistance={2.2}
      maxDistance={11.0}
      minPolarAngle={0.15}
      maxPolarAngle={Math.PI / 2 - 0.05} // Запрещаем инвесторам проваливаться сквозь асфальт
    />
  );
};

export const Scene: React.FC = () => {
  const currentVehicle = useSeatStore((s) => s.currentVehicle);
  const seats = useSeatStore((s) => s.seats);
  const isIntroActive = useSeatStore((s) => s.isIntroActive);
  const skipIntro = useSeatStore((s) => s.skipIntro);

  return (
    <Canvas
      dpr={[1, 1.5]} // Защита мобильных устройств от троттлинга на 3x Retina
      gl={{
        antialias: true,
        toneMapping: THREE.ACESFilmicToneMapping,
        toneMappingExposure: 1.1,
        powerPreference: 'high-performance',
      }}
      shadows
      onClick={() => {
        if (isIntroActive) skipIntro();
      }}
    >
      {/* 1. Реалистичный мягкий естественный рассеянный свет */}
      <ambientLight intensity={0.5} />
      <hemisphereLight args={['#F8FAFC', '#94A3B8', 0.45]} />

      {/* 2. Направленный солнечный луч через окна с мягкими тенями */}
      <directionalLight
        position={[6, 8, 5]}
        intensity={1.2}
        castShadow
        shadow-mapSize={[1024, 1024]}
        shadow-bias={-0.0001}
        shadow-camera-near={1}
        shadow-camera-far={20}
        shadow-camera-left={-5}
        shadow-camera-right={5}
        shadow-camera-top={5}
        shadow-camera-bottom={-5}
      />

      {/* 3. Мягкая подсветка прохода изнутри */}
      <pointLight position={[0, 1.7, 0]} intensity={0.3} distance={5} color="#F8FAFC" />

      {/* 4. Контроллер камеры с ограничениями и демпфированием */}
      <CameraController />

      {/* 5. Салон ТС и 3D-кресла */}
      <CabinModel vehicle={currentVehicle} />

      {seats.map((seat, index) => (
        <Seat3D key={seat.id} seat={seat} introDelay={index * 0.04} />
      ))}

      {/* 6. Контактные тени под кузовом и креслами */}
      <ContactShadows
        position={[0, -0.07, 0]}
        opacity={0.4}
        scale={12}
        blur={1.6}
        far={2.2}
        resolution={512}
        color="#0F172A"
      />
    </Canvas>
  );
};
