import { getTranslations } from 'next-intl/server';
import { setRequestLocale } from 'next-intl/server';
import { ExportPanel } from '@/components/export/export-panel';

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function ReportsPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('exportNs');

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-3xl font-bold text-primary">
          {t('title')}
        </h1>
        <p className="text-lg text-muted-foreground">
          {t('subtitle')}
        </p>
      </div>
      <ExportPanel />
    </div>
  );
}
