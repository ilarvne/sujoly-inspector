import { create } from 'zustand';
import { ZHAMBYL_CENTER } from '@/lib/constants';

interface MapState {
  viewport: { longitude: number; latitude: number; zoom: number };
  setViewport: (viewport: { longitude: number; latitude: number; zoom: number }) => void;
}

export const useMapStore = create<MapState>()((set) => ({
  viewport: { ...ZHAMBYL_CENTER },
  setViewport: (viewport) => set({ viewport }),
}));
