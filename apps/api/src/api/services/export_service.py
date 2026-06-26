"""Trilingual export service — CSV/GeoJSON/PDF generation (D-19–D-23).

Provides:
- export_structures_csv: StreamingResponse with UTF-8 BOM, trilingual headers, risk fields (D-20)
- export_structures_geojson: FeatureCollection with risk fields in properties (D-21)
- export_inspection_report_pdf: WeasyPrint + Jinja2 PDF with base64 photos (D-22)

All three formats support lang parameter (ru/kk/en) with server-side
translations via _TRANSLATIONS dict per D-23.

Security mitigations:
- T-03-18: CSV formula injection — prefix cells starting with =,+,-,@ with '
- T-03-20: PDF generation blocks event loop — use asyncio.to_thread() for WeasyPrint
"""

import asyncio
import base64
import csv
import io
import json
import uuid
from pathlib import Path

import structlog
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from api.services import risk_service, structure_service
from api.services.inspection_service import get_inspection

logger = structlog.get_logger(__name__)

# Templates directory (relative to this file's parent's parent → apps/api/templates)
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# ---------------------------------------------------------------------------
# Trilingual translations dict (D-23)
# ---------------------------------------------------------------------------
_TRANSLATIONS = {
    "ru": {
        "csv_headers": [
            "Название",
            "Тип",
            "Район",
            "Техническое состояние",
            "Износ (%)",
            "Интервал осмотра",
            "Статус ремонта",
            "Композитный балл",
        ],
        "report": {
            "title": "Отчёт об осмотрах гидротехнических сооружений",
            "structure_identity": "Идентификация сооружения",
            "name": "Название",
            "type": "Тип",
            "district": "Район",
            "water_source": "Источник водоснабжения",
            "technical_condition": "Техническое состояние",
            "wear_percentage": "Износ (%)",
            "inspection_details": "Детали осмотра",
            "inspector_name": "ФИО инспектора",
            "inspector_role": "Должность инспектора",
            "inspection_date": "Дата осмотра",
            "findings": "Результаты осмотра",
            "condition_at_inspection": "Состояние при осмотре",
            "photos": "Фотографии",
            "risk_assessment": "Оценка риска",
            "condition_score": "Балл состояния",
            "consequence_factor": "Фактор последствий",
            "seasonal_modifier": "Сезонный модификатор",
            "staleness_modifier": "Модификатор актуальности",
            "composite_score": "Композитный балл",
            "inspection_interval": "Интервал осмотра",
            "repair_status": "Статус ремонта",
            "red_flags": "Красные флаги",
            "provenance": "Происхождение данных",
        },
        "status_names": {
            "normal": "Нормальный",
            "inspection_required": "Требуется осмотр",
            "repair_required": "Требуется ремонт",
            "critical_condition": "Критическое состояние",
            "удовлетворительное": "Удовлетворительное",
            "неудовлетворительное": "Неудовлетворительное",
            "аварийное": "Аварийное",
        },
    },
    "kk": {
        "csv_headers": [
            "Атауы",
            "Түрі",
            "Аудан",
            "Техникалық жағдай",
            "Тозу (%)",
            "Тексеру аралығы",
            "Жөндеу мәртебесі",
            "Құрама балл",
        ],
        "report": {
            "title": "Гидротехникалық құрылымдарды тексеру баяндамасы",
            "structure_identity": "Құрылымды сәйкестендіру",
            "name": "Атауы",
            "type": "Түрі",
            "district": "Аудан",
            "water_source": "Су көзі",
            "technical_condition": "Техникалық жағдай",
            "wear_percentage": "Тозу (%)",
            "inspection_details": "Тексеру мәліметтері",
            "inspector_name": "Тексерушінің аты-жөні",
            "inspector_role": "Тексерушінің лауазымы",
            "inspection_date": "Тексеру күні",
            "findings": "Тексеру нәтижелері",
            "condition_at_inspection": "Тексерудегі жағдай",
            "photos": "Фотосуреттер",
            "risk_assessment": "Тәуекелді бағалау",
            "condition_score": "Жағдай баллы",
            "consequence_factor": "Зардап факторы",
            "seasonal_modifier": "Маусымдық модификатор",
            "staleness_modifier": "Өзектілік модификаторы",
            "composite_score": "Құрама балл",
            "inspection_interval": "Тексеру аралығы",
            "repair_status": "Жөндеу мәртебесі",
            "red_flags": "Қызыл жалаулар",
            "provenance": "Деректер шығу тегі",
        },
        "status_names": {
            "normal": "Қалыпты",
            "inspection_required": "Тексеру қажет",
            "repair_required": "Жөндеу қажет",
            "critical_condition": "Критикалық жағдай",
        },
    },
    "en": {
        "csv_headers": [
            "Name",
            "Type",
            "District",
            "Technical Condition",
            "Wear (%)",
            "Inspection Interval",
            "Repair Status",
            "Composite Score",
        ],
        "report": {
            "title": "Hydraulic Structure Inspection Report",
            "structure_identity": "Structure Identity",
            "name": "Name",
            "type": "Type",
            "district": "District",
            "water_source": "Water Source",
            "technical_condition": "Technical Condition",
            "wear_percentage": "Wear (%)",
            "inspection_details": "Inspection Details",
            "inspector_name": "Inspector Name",
            "inspector_role": "Inspector Role",
            "inspection_date": "Inspection Date",
            "findings": "Findings",
            "condition_at_inspection": "Condition at Inspection",
            "photos": "Photos",
            "risk_assessment": "Risk Assessment",
            "condition_score": "Condition Score",
            "consequence_factor": "Consequence Factor",
            "seasonal_modifier": "Seasonal Modifier",
            "staleness_modifier": "Staleness Modifier",
            "composite_score": "Composite Score",
            "inspection_interval": "Inspection Interval",
            "repair_status": "Repair Status",
            "red_flags": "Red Flags",
            "provenance": "Data Provenance",
        },
        "status_names": {
            "normal": "Normal",
            "inspection_required": "Inspection Required",
            "repair_required": "Repair Required",
            "critical_condition": "Critical Condition",
        },
    },
}


# ---------------------------------------------------------------------------
# CSV formula injection mitigation (T-03-18)
# ---------------------------------------------------------------------------

_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_csv_cell(value: str) -> str:
    """Prefix cells starting with dangerous characters with a single quote (T-03-18).

    Prevents CSV formula injection in Excel and other spreadsheet applications.
    Standard mitigation: prefix =,+,-,@ with single quote.
    """
    if value and str(value)[0] in _DANGEROUS_PREFIXES:
        return "'" + str(value)
    return str(value)


# ---------------------------------------------------------------------------
# CSV export (D-20)
# ---------------------------------------------------------------------------


async def export_structures_csv(
    lang: str = "ru",
    filters: dict | None = None,
) -> StreamingResponse:
    """Export structures as CSV with UTF-8 BOM and trilingual headers (D-20).

    Generates a CSV file with:
    - UTF-8 BOM prefix for Excel Cyrillic compatibility
    - Translated column headers per lang (D-23)
    - Structure fields + current risk assessment fields
    - CSV formula injection mitigation (T-03-18)

    Args:
        lang: Language code (ru/kk/en) for column headers
        filters: Optional dict with type, district, technical_condition, bbox keys

    Returns:
        StreamingResponse with text/csv content type and Content-Disposition header.
    """
    if filters is None:
        filters = {}

    # Fetch structures using existing list_structures (supports filters + bbox)
    items, total = await structure_service.list_structures(
        filters=filters,
        q=None,
        lang=lang,
        bbox=filters.get("bbox"),
        offset=0,
        limit=10000,
        format="json",
    )

    # Build CSV in memory
    buf = io.StringIO()
    # UTF-8 BOM for Excel Cyrillic compatibility (D-20)
    buf.write("\ufeff")

    writer = csv.writer(buf)
    headers = _TRANSLATIONS[lang]["csv_headers"]
    writer.writerow(headers)

    for struct in items:
        # Fetch latest risk assessment for this structure
        risk = await risk_service.get_latest_assessment(struct.id)

        # Lang-aware name column: use name_{lang}, fallback to name_ru (D-20 fix)
        lang_name = getattr(struct, f"name_{lang}", None) or getattr(struct, "name_ru", "") or ""
        row = [
            _sanitize_csv_cell(lang_name),
            _sanitize_csv_cell(getattr(struct, "type", "") or ""),
            _sanitize_csv_cell(getattr(struct, "district", "") or ""),
            _sanitize_csv_cell(getattr(struct, "technical_condition", "") or ""),
            _sanitize_csv_cell(str(getattr(struct, "wear_percentage", "") or "")),
            _sanitize_csv_cell(getattr(risk, "inspection_interval", "") or ""),
            _sanitize_csv_cell(getattr(risk, "repair_status", "") or ""),
            _sanitize_csv_cell(str(getattr(risk, "composite_score", "") or "")),
        ]
        writer.writerow(row)

    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8")]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=structures_{lang}.csv",
        },
    )


# ---------------------------------------------------------------------------
# GeoJSON export (D-21)
# ---------------------------------------------------------------------------


async def export_structures_geojson(
    lang: str = "ru",
    filters: dict | None = None,
) -> dict:
    """Export structures as GeoJSON FeatureCollection with risk fields (D-21).

    Reuses the GeoJSON FeatureCollection pattern from Phase 2 (D-16)
    with additional risk assessment fields in properties.

    Args:
        lang: Language code (ru/kk/en)
        filters: Optional dict with type, district, technical_condition, bbox keys

    Returns:
        Dict with FeatureCollection structure.
    """
    if filters is None:
        filters = {}

    items, total = await structure_service.list_structures(
        filters=filters,
        q=None,
        lang=lang,
        bbox=filters.get("bbox"),
        offset=0,
        limit=10000,
        format="json",
    )

    features = []
    for struct in items:
        # Build properties from structure fields
        properties = {
            "id": str(struct.id),
            "name_ru": getattr(struct, "name_ru", None),
            "name_kk": getattr(struct, "name_kk", None),
            "name_en": getattr(struct, "name_en", None),
            "type": getattr(struct, "type", None),
            "district": getattr(struct, "district", None),
            "water_source": getattr(struct, "water_source", None),
            "technical_condition": getattr(struct, "technical_condition", None),
            "wear_percentage": getattr(struct, "wear_percentage", None),
            "commissioning_year": getattr(struct, "commissioning_year", None),
            "cadastral_number": getattr(struct, "cadastral_number", None),
            "structure_count": getattr(struct, "structure_count", None),
            "status": getattr(struct, "status", None),
        }

        # Fetch and include risk assessment fields (D-21)
        risk = await risk_service.get_latest_assessment(struct.id)
        if risk is not None:
            properties["inspection_interval"] = risk.inspection_interval
            properties["repair_status"] = risk.repair_status
            properties["composite_score"] = risk.composite_score
        else:
            properties["inspection_interval"] = None
            properties["repair_status"] = None
            properties["composite_score"] = None

        # Geometry from structure — build GeoJSON Point from lat/lon
        lat = getattr(struct, "latitude", None)
        lon = getattr(struct, "longitude", None)
        if lat is not None and lon is not None:
            geometry = {"type": "Point", "coordinates": [lon, lat]}
        else:
            geometry = None

        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
            }
        )

    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# PDF export (D-22)
# ---------------------------------------------------------------------------


async def export_inspection_report_pdf(
    inspection_id: uuid.UUID,
    lang: str = "ru",
    minio_service=None,
) -> StreamingResponse:
    """Generate a PDF inspection report via WeasyPrint + Jinja2 (D-22).

    Renders a trilingual HTML template with structure identity, inspection
    details, findings, photos (base64-embedded from MinIO), and risk assessment
    summary. WeasyPrint converts HTML to PDF.

    Uses asyncio.to_thread() for the synchronous WeasyPrint call to avoid
    blocking the async event loop (T-03-20 mitigation).

    Args:
        inspection_id: UUID of the inspection to generate report for
        lang: Language code (ru/kk/en) for template selection
        minio_service: MinIOService instance for downloading photos

    Returns:
        StreamingResponse with application/pdf content type.

    Raises:
        ValueError: If inspection not found
    """
    # Fetch inspection with photos
    inspection = await get_inspection(inspection_id)
    if inspection is None:
        raise ValueError(f"Inspection '{inspection_id}' not found")

    # Fetch structure details
    struct = await structure_service.get_structure(inspection.structure_id)

    # Fetch risk assessment
    risk = await risk_service.get_latest_assessment(inspection.structure_id)

    # Download photos from MinIO and base64 encode for HTML embedding
    photos_data = []
    if minio_service is not None and hasattr(inspection, "photos"):
        for photo in inspection.photos:
            try:
                with minio_service.client.get_object(
                    photo.minio_bucket, photo.minio_object_key
                ) as response:
                    photo_bytes = response.read()
                b64_data = base64.b64encode(photo_bytes).decode("ascii")
                photos_data.append(
                    {
                        "data": b64_data,
                        "caption": getattr(photo, "caption", "") or "",
                        "photo_type": getattr(photo, "photo_type", "overview"),
                    }
                )
            except Exception:
                logger.warning(
                    "photo_download_failed",
                    bucket=photo.minio_bucket,
                    key=photo.minio_object_key,
                )

    # Render Jinja2 template
    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
    template_name = f"inspection_report_{lang}.html"
    template = env.get_template(template_name)

    html_content = template.render(
        structure=struct,
        inspection=inspection,
        risk=risk,
        photos=photos_data,
        labels=_TRANSLATIONS[lang]["report"],
        status_names=_TRANSLATIONS[lang]["status_names"],
    )

    # Generate PDF in a thread to avoid blocking the event loop (T-03-20)
    pdf_bytes = await asyncio.to_thread(
        lambda: HTML(string=html_content).write_pdf()
    )

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=inspection_{inspection_id}_{lang}.pdf",
        },
    )
