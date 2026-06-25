import { getTranslations } from 'next-intl/server';
import { setRequestLocale } from 'next-intl/server';
import { MapView } from '@/components/map/map-view';
import { FilterPanel } from '@/components/map/filter-panel';
import { PassportPanel } from '@/components/map/passport-panel';

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function MapPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('map');

  return (
    <div className="flex h-[calc(100vh-7.5rem)] flex-col gap-4">
      <div>
        <h1 className="font-display text-3xl font-bold text-primary">
          {t('title')}
        </h1>
        <p className="text-lg text-muted-foreground">
          {t('subtitle')}
        </p>
      </div>
      <div className="relative flex-1 overflow-hidden rounded-lg border">
        <MapView />
        <FilterPanel />
        <PassportPanel />
      </div>
    </div>
  );
}
