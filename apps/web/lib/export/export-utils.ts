import Papa from 'papaparse';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import type {
  StructureFeature,
  StructureCollection,
  StructureDetail,
  InspectionRecord,
} from '@/lib/api/types';

export function generateCSV(features: StructureFeature[]): string {
  const data = features.map((f) => ({
    id: f.properties.id,
    name: f.properties.name.ru,
    name_kk: f.properties.name.kk,
    name_en: f.properties.name.en,
    type: f.properties.type,
    condition: f.properties.condition,
    inspectionStatus: f.properties.inspectionStatus,
    district: f.properties.district,
    basin: f.properties.basin,
    source: f.properties.provenance.source,
    confidence: f.properties.provenance.confidence,
  }));
  const csv = Papa.unparse(data);
  return '\uFEFF' + csv;
}

export function generateGeoJSON(collection: StructureCollection): string {
  return JSON.stringify(collection, null, 2);
}

export function generatePDF(
  structure: StructureDetail,
  inspections: InspectionRecord[],
  title: string = 'Inspection Report',
): void {
  const doc = new jsPDF();

  doc.setFontSize(18);
  doc.text(title, 14, 22);

  doc.setFontSize(12);
  doc.text(`Structure: ${structure.name.ru}`, 14, 32);
  doc.text(`ID: ${structure.id}`, 14, 40);
  doc.text(`Type: ${structure.type}`, 14, 48);
  doc.text(`Condition: ${structure.condition}`, 14, 56);
  doc.text(`District: ${structure.district}`, 14, 64);

  if (structure.coordinates) {
    doc.text(
      `Coordinates: ${structure.coordinates.lon.toFixed(4)}, ${structure.coordinates.lat.toFixed(4)}`,
      14,
      72,
    );
  }

  autoTable(doc, {
    head: [['Date', 'Inspector', 'Condition', 'Findings']],
    body: inspections.map((i) => [
      i.date,
      i.inspectorName,
      i.conditionAtInspection,
      i.findings.substring(0, 80),
    ]),
    startY: 82,
    styles: { fontSize: 9 },
    headStyles: { fillColor: [11, 79, 108] },
  });

  doc.save(`inspection-report-${structure.id}.pdf`);
}

export function downloadBlob(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
