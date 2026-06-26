import { getTranslations } from 'next-intl/server';
import { setRequestLocale } from 'next-intl/server';
import { FieldInspectionForm } from '@/components/field/field-inspection-form';
import { SyncQueuePanel } from '@/components/field/sync-queue-panel';
import { PermissionGuard } from '@/components/auth/permission-guard';
import { LoginForm } from '@/components/auth/login-form';

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function FieldPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('field');

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-xl font-bold text-primary sm:text-2xl lg:text-3xl">
          {t('title')}
        </h1>
        <p className="text-sm text-muted-foreground sm:text-base lg:text-lg">
          {t('subtitle')}
        </p>
      </div>

      <PermissionGuard
        roles={['inspector', 'engineer', 'admin']}
        fallback={
          <div className="space-y-4">
            <p className="text-muted-foreground">{t('noStructures')}</p>
            <LoginForm />
          </div>
        }
      >
        <div className="space-y-6">
          <FieldInspectionForm />
          <SyncQueuePanel />
        </div>
      </PermissionGuard>
    </div>
  );
}
