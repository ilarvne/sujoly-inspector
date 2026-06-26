'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { usePathname, useRouter } from '@/i18n/navigation';

const PUBLIC_ROUTES = ['/login', '/offline'];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const pathname = usePathname();
  const router = useRouter();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;

    const isPublic = PUBLIC_ROUTES.some((r) => pathname === r);

    if (!user && !isPublic) {
      router.replace('/login');
    } else if (user && pathname === '/login') {
      router.replace('/map');
    }
  }, [hydrated, user, pathname, router]);

  if (!hydrated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground animate-pulse">Loading...</div>
      </div>
    );
  }

  const isPublic = PUBLIC_ROUTES.some((r) => pathname === r);

  if (!user && !isPublic) return null;
  if (user && pathname === '/login') return null;

  return <>{children}</>;
}
