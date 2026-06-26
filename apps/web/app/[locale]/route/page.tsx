import { getTranslations, setRequestLocale } from 'next-intl/server';
import { RouteView } from '@/components/route/route-view';

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function RoutePage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('route');

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-primary sm:text-3xl">
          {t('title')}
        </h1>
        <p className="text-muted-foreground">{t('subtitle')}</p>
      </div>
      <RouteView />
    </div>
  );
}
