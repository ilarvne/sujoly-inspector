import { create } from 'zustand';

export type WeatherMode = 'normal' | 'heavy_rain' | 'flood_season';

interface WeatherStore {
  mode: WeatherMode;
  setMode: (mode: WeatherMode) => void;
}

export const useWeatherStore = create<WeatherStore>()((set) => ({
  mode: 'normal',
  setMode: (mode) => set({ mode }),
}));
