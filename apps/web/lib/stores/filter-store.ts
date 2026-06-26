import { create } from 'zustand';

interface FilterState {
  district: string | null;
  basin: string | null;
  type: string | null;
  condition: string | null;
  inspectionStatus: string | null;
  setFilter: (key: keyof Omit<FilterState, 'setFilter' | 'resetFilters'>, value: string | null) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>()((set) => ({
  district: null,
  basin: null,
  type: null,
  condition: null,
  inspectionStatus: null,
  setFilter: (key, value) => set({ [key]: value } as Partial<FilterState>),
  resetFilters: () =>
    set({
      district: null,
      basin: null,
      type: null,
      condition: null,
      inspectionStatus: null,
    }),
}));
