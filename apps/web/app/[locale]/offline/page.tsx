import { getTranslations } from 'next-intl/server';

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function OfflinePage({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'pwa' });

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <div className="text-6xl">📡</div>
      <h1 className="font-display text-2xl font-bold text-primary">
        {t('offlineTitle')}
      </h1>
      <p className="text-center text-muted-foreground max-w-md">
        {t('offlineMessage')}
      </p>
      <a
        href={`/${locale}`}
        className="rounded-md bg-primary px-6 py-2 text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        {t('retryConnection')}
      </a>
    </div>
  );
}
