'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { CheckIcon, LinkIcon, XCircleIcon } from 'lucide-react';
import { useMatchResult, mockSubmitReviewAction } from '@/lib/api/client';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useDiscoveryStore } from '@/lib/stores/discovery-store';
import { useQueryClient } from '@tanstack/react-query';
import type { ReviewAction, ReviewStatus } from '@/lib/api/types';

const statusColors: Record<ReviewStatus, string> = {
  pending: '#eab308',
  accepted: '#22c55e',
  linked: '#2563eb',
  rejected: '#ef4444',
};

export function ReviewActions() {
  const t = useTranslations('discovery');
  const { selectedCandidateId, markReviewed } = useDiscoveryStore();
  const { data: match } = useMatchResult(selectedCandidateId);
  const { user, hasRole } = useAuthStore();
  const queryClient = useQueryClient();
  const [dialogAction, setDialogAction] = useState<ReviewAction | null>(null);
  const [reason, setReason] = useState('');
  const [success, setSuccess] = useState(false);

  const canReview = hasRole('admin', 'engineer');
  const status = match?.reviewStatus ?? 'pending';
  const hasExisting = match?.existingStructureId != null;
  const isReviewed = status !== 'pending';

  const handleOpenDialog = (action: ReviewAction) => {
    setDialogAction(action);
    setReason('');
    setSuccess(false);
  };

  const handleSubmit = () => {
    if (!dialogAction || !selectedCandidateId || !user) return;
    mockSubmitReviewAction(selectedCandidateId, dialogAction, user.name, reason);
    markReviewed(selectedCandidateId);
    queryClient.invalidateQueries({ queryKey: ['discovery'] });
    setSuccess(true);
    setDialogAction(null);
  };

  if (!selectedCandidateId) {
    return null;
  }

  if (!canReview) {
    if (!user) {
      return (
        <Alert>
          <AlertDescription>{t('review.loginRequired')}</AlertDescription>
        </Alert>
      );
    }
    return (
      <Alert variant="destructive">
        <AlertDescription>{t('review.permissionDenied')}</AlertDescription>
      </Alert>
    );
  }

  const confirmMessages: Record<ReviewAction, string> = {
    accept: t('review.confirmAccept'),
    link: t('review.confirmLink'),
    reject: t('review.confirmReject'),
  };

  return (
    <div className="space-y-3">
      {success && (
        <Alert>
          <AlertDescription>{t('review.reviewSuccess')}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold">{t('table.status')}</span>
        <Badge style={{ backgroundColor: statusColors[status] }} className="text-white">
          {t(`review.${status}`)}
        </Badge>
      </div>

      {!isReviewed && (
        <div className="flex gap-2">
          <Button
            onClick={() => handleOpenDialog('accept')}
            className="flex-1 bg-green-600 hover:bg-green-700"
            data-testid="review-accept"
          >
            <CheckIcon className="size-4" />
            {t('review.accept')}
          </Button>
          {hasExisting && (
            <Button
              onClick={() => handleOpenDialog('link')}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
              data-testid="review-link"
            >
              <LinkIcon className="size-4" />
              {t('review.link')}
            </Button>
          )}
          <Button
            onClick={() => handleOpenDialog('reject')}
            variant="outline"
            className="flex-1 border-red-500 text-red-600 hover:bg-red-50"
            data-testid="review-reject"
          >
            <XCircleIcon className="size-4" />
            {t('review.reject')}
          </Button>
        </div>
      )}

      <Dialog open={dialogAction !== null} onOpenChange={(open) => !open && setDialogAction(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t(`review.${dialogAction}`)}</DialogTitle>
            <DialogDescription>
              {dialogAction && confirmMessages[dialogAction]}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>{t('review.reason')}</Label>
            <Textarea
              placeholder={t('review.reasonPlaceholder')}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              data-testid="review-reason"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogAction(null)}>
              {t('review.cancel')}
            </Button>
            <Button onClick={handleSubmit} data-testid="review-submit">
              {t('review.submit')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
