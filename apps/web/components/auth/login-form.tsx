'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/lib/stores/auth-store';
import type { UserRole } from '@/lib/stores/auth-store';

const roles: UserRole[] = ['admin', 'engineer', 'inspector', 'viewer'];
const roleLabelKeys: Record<UserRole, string> = {
  admin: 'roleAdmin',
  engineer: 'roleEngineer',
  inspector: 'roleInspector',
  viewer: 'roleViewer',
};
const roleDescKeys: Record<UserRole, string> = {
  admin: 'roleAdminDesc',
  engineer: 'roleEngineerDesc',
  inspector: 'roleInspectorDesc',
  viewer: 'roleViewerDesc',
};

export function LoginForm() {
  const t = useTranslations('auth');
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);

  const handleSignIn = () => {
    if (selectedRole) {
      login(selectedRole);
      router.push('/map');
    }
  };

  return (
    <div className="w-full max-w-2xl space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {roles.map((role) => (
          <Card
            key={role}
            data-testid={`role-card-${role}`}
            className={`cursor-pointer transition-all ${
              selectedRole === role
                ? 'border-primary ring-2 ring-primary/20'
                : 'hover:border-primary/50'
            }`}
            onClick={() => setSelectedRole(role)}
          >
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{t(roleLabelKeys[role])}</CardTitle>
                <Badge variant={selectedRole === role ? 'default' : 'secondary'}>
                  {role}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t(roleDescKeys[role])}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Button
        className="w-full"
        size="lg"
        disabled={!selectedRole}
        onClick={handleSignIn}
        data-testid="signin-button"
      >
        {t('signIn')}
      </Button>
    </div>
  );
}
