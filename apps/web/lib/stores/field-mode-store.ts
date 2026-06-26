import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface FieldModeState {
  fieldModeEnabled: boolean;
  lastSyncAt: string | null;
  enableFieldMode: () => void;
  disableFieldMode: () => void;
  setLastSyncAt: (time: string) => void;
}

export const useFieldModeStore = create<FieldModeState>()(
  persist(
    (set) => ({
      fieldModeEnabled: false,
      lastSyncAt: null,
      enableFieldMode: () => set({ fieldModeEnabled: true }),
      disableFieldMode: () => set({ fieldModeEnabled: false }),
      setLastSyncAt: (time) => set({ lastSyncAt: time }),
    }),
    { name: 'sujoly-field-mode' }
  )
);
