'use client';

import { useAuthStore } from '@/lib/stores/auth-store';
import type { UserRole } from '@/lib/stores/auth-store';

export function PermissionGuard({
  roles,
  children,
  fallback = null,
}: {
  roles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const hasRole = useAuthStore((s) => s.hasRole);
  return <>{hasRole(...roles) ? children : fallback}</>;
}
