import { setRequestLocale } from 'next-intl/server';
import { ObjectsView } from '@/components/objects/objects-view';

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function ObjectsPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);

  return <ObjectsView />;
}
