'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useOverrides } from '@/lib/api/client';
import type { OverrideField } from '@/lib/api/types';

const overrideSchema = z.object({
  field: z.enum(['inspection_interval', 'repair_status']),
  newValue: z.string().min(1, 'Value is required'),
  reason: z.string().min(10, 'Reason must be at least 10 characters'),
});

type OverrideFormData = z.infer<typeof overrideSchema>;

export function EngineerOverrideDialog({
  structureId,
  open,
  onOpenChange,
}: {
  structureId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const t = useTranslations('override');
  const { data: overrides, isLoading } = useOverrides(structureId);
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<OverrideFormData>({
    resolver: zodResolver(overrideSchema),
    defaultValues: {
      field: 'inspection_interval',
      newValue: '',
      reason: '',
    },
  });

  const selectedField = watch('field') as OverrideField;

  const onSubmit = (_data: OverrideFormData) => {
    onOpenChange(false);
    reset();
  };

  const fieldLabelKey = (field: OverrideField) =>
    field === 'inspection_interval' ? 'inspectionInterval' : 'repairStatus';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t('title')}</DialogTitle>
          <DialogDescription>{structureId}</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label>{t('field')}</Label>
            <Select
              value={selectedField}
              onValueChange={(v) => setValue('field', v as OverrideField)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="inspection_interval">
                  {t('inspectionInterval')}
                </SelectItem>
                <SelectItem value="repair_status">
                  {t('repairStatus')}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>{t('originalValue')}</Label>
            <Input
              value={selectedField === 'inspection_interval' ? '12 months' : 'repair_required'}
              readOnly
              className="bg-muted"
            />
          </div>

          <div className="space-y-2">
            <Label>{t('newValue')}</Label>
            <Input
              {...register('newValue')}
              placeholder={selectedField === 'inspection_interval' ? 'e.g., 6 months' : 'e.g., monitor'}
            />
            {errors.newValue && (
              <p className="text-xs text-destructive">{t('valueRequired')}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>{t('reason')}</Label>
            <Textarea
              {...register('reason')}
              placeholder={t('reasonPlaceholder')}
              rows={4}
            />
            {errors.reason && (
              <p className="text-xs text-destructive">{t('reasonRequired')}</p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {t('cancel')}
            </Button>
            <Button type="submit">{t('submit')}</Button>
          </DialogFooter>
        </form>

        <Separator />

        <div className="space-y-2">
          <h4 className="text-sm font-semibold">{t('provenanceLog')}</h4>
          {isLoading ? (
            <p className="text-xs text-muted-foreground">{t('loading')}</p>
          ) : !overrides || overrides.length === 0 ? (
            <p className="text-xs text-muted-foreground">{t('noOverrides')}</p>
          ) : (
            <div className="space-y-3">
              {overrides.map((ov) => (
                <div key={ov.id} className="rounded border p-2 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="font-semibold">{t(fieldLabelKey(ov.field))}</span>
                    <span className="text-muted-foreground">{ov.timestamp}</span>
                  </div>
                  <div className="text-muted-foreground">
                    {ov.originalValue} → <span className="font-medium text-foreground">{ov.newValue}</span>
                  </div>
                  <p>{ov.reason}</p>
                  <div className="text-muted-foreground">{t('engineer')}: {ov.engineerName}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
