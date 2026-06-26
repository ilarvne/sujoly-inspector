import { create } from 'zustand';

interface ConnectivityState {
  isOnline: boolean;
  pendingSyncCount: number;
  setOnline: (online: boolean) => void;
  setPendingSyncCount: (count: number) => void;
}

export const useConnectivityStore = create<ConnectivityState>((set) => ({
  isOnline: true,
  pendingSyncCount: 0,
  setOnline: (online) => set({ isOnline: online }),
  setPendingSyncCount: (count) => set({ pendingSyncCount: count }),
}));

export function initConnectivity(): void {
  if (typeof navigator !== 'undefined') {
    useConnectivityStore.getState().setOnline(navigator.onLine);
  }
}
