import { create } from 'zustand';
import { SeatData3D, CameraPreset, VehicleConfig3D } from './types';
import { SPRINTER_19_SEATS, SPRINTER_VEHICLE } from './mockData3D';

interface SeatStoreState {
  currentVehicle: VehicleConfig3D;
  seats: SeatData3D[];
  selectedSeatIds: string[];
  maxSelectedSeats: number;
  hoveredSeat: SeatData3D | null;
  selectedRow: number | null;
  activePreset: CameraPreset;
  cameraTargetPos: [number, number, number];
  cameraLookAt: [number, number, number];
  isIntroActive: boolean;
  is2DFallback: boolean;
  notification: string | null;

  toggleSeat: (seatId: string) => void;
  setHoveredSeat: (seat: SeatData3D | null) => void;
  setCameraPreset: (preset: CameraPreset) => void;
  flyToSeat: (seat: SeatData3D) => void;
  skipIntro: () => void;
  toggle2DFallback: () => void;
  clearNotification: () => void;
}

export const useSeatStore = create<SeatStoreState>((set, get) => ({
  currentVehicle: SPRINTER_VEHICLE,
  seats: SPRINTER_19_SEATS,
  selectedSeatIds: [],
  maxSelectedSeats: 3,
  hoveredSeat: null,
  selectedRow: null,
  activePreset: 'hero',
  cameraTargetPos: SPRINTER_VEHICLE.cameraPresets.hero.position,
  cameraLookAt: SPRINTER_VEHICLE.cameraPresets.hero.lookAt,
  isIntroActive: true,
  is2DFallback: false,
  notification: null,

  toggleSeat: (seatId: string) => {
    const { seats, selectedSeatIds, maxSelectedSeats } = get();
    const seat = seats.find((s) => s.id === seatId);
    if (!seat || seat.status === 'occupied' || seat.status === 'blocked') return;

    if (selectedSeatIds.includes(seatId)) {
      const nextSelected = selectedSeatIds.filter((id) => id !== seatId);
      const lastSeat = seats.find((s) => s.id === nextSelected[nextSelected.length - 1]);
      set({
        selectedSeatIds: nextSelected,
        selectedRow: lastSeat ? lastSeat.row : null,
      });
    } else {
      if (selectedSeatIds.length >= maxSelectedSeats) {
        set({ notification: `Максимум мест для бронирования: ${maxSelectedSeats}` });
        return;
      }
      set({
        selectedSeatIds: [...selectedSeatIds, seatId],
        selectedRow: seat.row,
      });
      // Плавный переход камеры ближе к выбранному месту
      get().flyToSeat(seat);
    }
  },

  setHoveredSeat: (seat) => {
    set({ hoveredSeat: seat });
  },

  setCameraPreset: (preset) => {
    const { currentVehicle } = get();
    const cfg = currentVehicle.cameraPresets[preset];
    if (cfg) {
      set({
        activePreset: preset,
        cameraTargetPos: cfg.position,
        cameraLookAt: cfg.lookAt,
      });
    }
  },

  flyToSeat: (seat) => {
    const [x, y, z] = seat.position;
    // Ракурс 3/4 чуть выше и правее кресла
    set({
      cameraTargetPos: [x + 1.2, y + 1.4, z + 1.3],
      cameraLookAt: [x, y + 0.4, z],
      activePreset: 'hero',
    });
  },

  skipIntro: () => {
    set({ isIntroActive: false });
  },

  toggle2DFallback: () => set((state) => ({ is2DFallback: !state.is2DFallback })),
  clearNotification: () => set({ notification: null }),
}));
