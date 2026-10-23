export type SeatStatus =
  | 'available'
  | 'selected'
  | 'occupied'
  | 'blocked'
  | 'disabled';

export type SeatCategory =
  | 'window'
  | 'aisle'
  | 'extra_legroom'
  | 'limited_recline'
  | 'emergency_exit'
  | 'family'
  | 'vip'
  | 'standard';

export interface SeatData3D {
  id: string;
  number: string;
  row: number;
  col: number;
  category: SeatCategory;
  price: number;
  status: SeatStatus;
  features: string[];
  position: [number, number, number];
  rotationY?: number;
}

export type CameraPreset = 'hero' | 'top' | 'driver' | 'reset';

export interface VehicleConfig3D {
  id: string;
  name: string;
  type: 'sprinter_19';
  carrierName: string;
  totalSeats: number;
  dimensions: {
    length: number;
    width: number;
    height: number;
  };
  cameraPresets: Record<CameraPreset, { position: [number, number, number]; lookAt: [number, number, number] }>;
}
