import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type UserRole = 'admin' | 'engineer' | 'inspector' | 'viewer';

export interface AuthUser {
  id: string;
  name: string;
  role: UserRole;
}

interface AuthState {
  user: AuthUser | null;
  login: (role: UserRole) => void;
  logout: () => void;
  hasRole: (...roles: UserRole[]) => boolean;
}

const mockUsers: Record<UserRole, AuthUser> = {
  admin: { id: 'u-admin', name: 'Administrator', role: 'admin' },
  engineer: { id: 'u-engineer', name: 'Engineer', role: 'engineer' },
  inspector: { id: 'u-inspector', name: 'Inspector', role: 'inspector' },
  viewer: { id: 'u-viewer', name: 'Viewer', role: 'viewer' },
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      login: (role) => set({ user: mockUsers[role] }),
      logout: () => set({ user: null }),
      hasRole: (...roles) => {
        const user = get().user;
        return user !== null && roles.includes(user.role);
      },
    }),
    { name: 'sujoly-auth' }
  )
);
