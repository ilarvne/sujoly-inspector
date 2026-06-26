import { getTranslations, setRequestLocale } from 'next-intl/server';
import { LoginForm } from '@/components/auth/login-form';

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function LoginPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('auth');

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
      <div className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-primary">
          {t('loginTitle')}
        </h1>
        <p className="text-lg text-muted-foreground">
          {t('loginSubtitle')}
        </p>
      </div>
      <LoginForm />
    </div>
  );
}
