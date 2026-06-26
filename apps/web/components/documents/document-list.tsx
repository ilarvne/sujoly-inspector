'use client';

import { useTranslations } from 'next-intl';
import { DownloadIcon, FileIcon } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useDocuments } from '@/lib/api/client';
import { format, parseISO } from 'date-fns';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentList({ structureId }: { structureId: string }) {
  const t = useTranslations('documents');
  const { data: documents, isLoading } = useDocuments(structureId);

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">{t('loading')}</div>;
  }

  if (!documents || documents.length === 0) {
    return <div className="p-4 text-muted-foreground">{t('noDocuments')}</div>;
  }

  return (
    <ScrollArea className="h-[300px] w-full pr-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[40%]">{t('filename')}</TableHead>
            <TableHead>{t('fileType')}</TableHead>
            <TableHead>{t('fileSize')}</TableHead>
            <TableHead>{t('uploadedBy')}</TableHead>
            <TableHead>{t('uploadedAt')}</TableHead>
            <TableHead className="w-12" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.id}>
              <TableCell className="flex items-center gap-2 font-medium">
                <FileIcon className="size-4 text-muted-foreground" />
                {doc.filename}
              </TableCell>
              <TableCell>
                <Badge variant="secondary">{doc.fileType}</Badge>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatFileSize(doc.fileSize)}
              </TableCell>
              <TableCell className="text-muted-foreground">{doc.uploadedBy}</TableCell>
              <TableCell className="text-muted-foreground">
                {format(parseISO(doc.uploadedAt), 'dd MMM yyyy')}
              </TableCell>
              <TableCell>
                <a
                  href={doc.downloadUrl}
                  className="inline-flex items-center text-primary hover:text-primary/80"
                  aria-label={t('download')}
                >
                  <DownloadIcon className="size-4" />
                </a>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </ScrollArea>
  );
}
