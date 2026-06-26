'use client';

import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { Sidebar } from './sidebar';
import { useTranslations } from 'next-intl';

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const t = useTranslations('nav');

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="text-primary-foreground hover:bg-primary-foreground/10 lg:hidden"
        onClick={() => setOpen(true)}
        aria-label={t('title')}
      >
        <Menu className="h-5 w-5" aria-hidden="true" />
      </Button>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <span className="font-display text-sm font-semibold">{t('title')}</span>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setOpen(false)}
              aria-label="Close"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
          <Sidebar onNavigate={() => setOpen(false)} />
        </SheetContent>
      </Sheet>
    </>
  );
}
