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
    <div className="flex h-[calc(100vh-6rem)] flex-col gap-2 sm:h-[calc(100vh-7.5rem)] sm:gap-4">
      <div>
        <h1 className="font-display text-xl font-bold text-primary sm:text-2xl lg:text-3xl">
          {t('title')}
        </h1>
        <p className="text-sm text-muted-foreground sm:text-base lg:text-lg">
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
