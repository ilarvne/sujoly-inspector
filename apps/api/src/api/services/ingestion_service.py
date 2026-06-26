"""Kazvodhoz spreadsheet ingestion service.

Provides:
- parse_kazvodhoz_sheet: parse 'Корректировка' sheet, skip headers/summaries
- enrich_with_cross_sheet_data: merge data from 'каналы' and 'Лист1' sheets
- bulk_insert_structures: sync bulk insert with provenance + idempotency

Decisions implemented:
- D-01/D-02: NULL geometry (no coordinates in spreadsheet)
- D-07: StructureFactModel rows for each spreadsheet column
- D-09: type='canal' for all records
- D-17: sync psycopg connection for bulk loading
- D-18: cross-reference all 3 sheets using row number as join key
- D-19: idempotent ingestion (check source_reference in provenance)
- D-20: provenance per structure with source_type='kazvodhoz_spreadsheet'
"""

import structlog
import xlrd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.config.settings import settings
from api.models.provenance import ProvenanceModel
from api.models.structure import StructureFactModel, StructureModel

logger = structlog.get_logger(__name__)


def _convert_cell(value):
    """Convert xlrd float cell values to int when they are whole numbers (Pitfall #1).

    xlrd returns all numeric cells as Python floats. Year '1973' becomes 1973.0.
    This converts 1973.0 → 1973 (int) but preserves 2.5 → 2.5 (float).
    """
    if isinstance(value, float) and value == int(value):
        return int(value)
    return value


def _safe_str(value):
    """Safely convert a cell value to string, returning None for empty values."""
    if value is None or value == "" or (isinstance(value, float) and value == 0.0 and not str(value)):
        return None
    result = str(value).strip()
    return result if result else None


def _safe_float(value):
    """Safely convert a cell value to float, returning None for empty/invalid values."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_kazvodhoz_sheet(sheet) -> list[dict]:
    """Parse the 'Корректировка' sheet, skipping headers and summary rows.

    Sheet structure (444 total rows):
    - Rows 0-4: Multi-row headers
    - Row 5: Sub-header continuation
    - Row 6: Column number indicator (1.0, 2.0, ...) — NOT data, SKIP
    - Row 7+: Data rows interspersed with group/category headers
    - Bottom rows: Summary totals

    Args:
        sheet: xlrd.sheet.Sheet — the 'Корректировка' worksheet

    Returns:
        List of dicts with keys: row_num, name, commissioning_year, water_source,
        capacity_m3s, total_length_before_km, earthwork_length_km, lined_length_km,
        total_length_after_km, notes, facts
    """
    records = []

    for row_idx in range(7, sheet.nrows):  # Start after column number row (row 6)
        col0 = sheet.cell_value(row_idx, 0)

        # Skip non-data rows: group/category headers have string col0 (Pitfall #2)
        if not isinstance(col0, float) or col0 < 1 or col0 > 440:
            continue

        # Skip rows with empty name (col 1) — summary rows (Pitfall #2)
        col1 = sheet.cell_value(row_idx, 1)
        if not col1 or str(col1).strip() == "":
            continue

        row_num = int(col0)
        name = _safe_str(col1)
        commissioning_year_raw = sheet.cell_value(row_idx, 2)
        commissioning_year = _convert_cell(commissioning_year_raw) if commissioning_year_raw else None
        water_source = _safe_str(sheet.cell_value(row_idx, 3))
        capacity_m3s = _safe_float(sheet.cell_value(row_idx, 4))
        total_length_before_km = _safe_float(sheet.cell_value(row_idx, 5))
        earthwork_length_km = _safe_float(sheet.cell_value(row_idx, 6))
        lined_length_km = _safe_float(sheet.cell_value(row_idx, 7))
        total_length_after_km = _safe_float(sheet.cell_value(row_idx, 9))
        notes = _safe_str(sheet.cell_value(row_idx, 12))

        # Collect all non-empty cell values into a facts dict (D-07)
        facts = {}
        for col_idx in range(sheet.ncols):
            cell_val = sheet.cell_value(row_idx, col_idx)
            if cell_val is not None and cell_val != "":
                facts[f"col_{col_idx}"] = _convert_cell(cell_val)

        record = {
            "row_num": row_num,
            "name": name,
            "commissioning_year": commissioning_year,
            "water_source": water_source,
            "capacity_m3s": capacity_m3s,
            "total_length_before_km": total_length_before_km,
            "earthwork_length_km": earthwork_length_km,
            "lined_length_km": lined_length_km,
            "total_length_after_km": total_length_after_km,
            "notes": notes,
            "facts": facts,
        }
        records.append(record)

    logger.info("parsed_kazvodhoz_sheet", record_count=len(records))
    return records


def enrich_with_cross_sheet_data(records: list[dict], sheet_kanaly, sheet_list1) -> list[dict]:
    """Enrich 'Корректировка' records with data from 'каналы' and 'Лист1' sheets.

    Cross-references all 3 sheets using col 0 (row number) as join key (D-18).

    'каналы' (22 cols) provides:
    - district (col 15), rural_district (col 16), wear_percentage (col 17),
      technical_condition (col 18), cadastral_number (col 19), state_act (col 20)

    'Лист1' (19 cols) provides:
    - canal_parameters (col 16), structure_count (col 17), year_accepted (col 18)

    Prefers 'каналы' data, falls back to 'Лист1' where overlap exists.

    Args:
        records: list of dicts from parse_kazvodhoz_sheet
        sheet_kanaly: xlrd Sheet for 'каналы'
        sheet_list1: xlrd Sheet for 'Лист1'

    Returns:
        Enriched records with district, wear_percentage, technical_condition,
        cadastral_number, structure_count, rural_district, canal_parameters
    """
    # Build lookup by row number from 'каналы' sheet
    kanaly_lookup = {}
    for r in range(5, sheet_kanaly.nrows):
        col0 = sheet_kanaly.cell_value(r, 0)
        if isinstance(col0, float) and 1 <= col0 <= 440:
            kanaly_lookup[int(col0)] = {
                "district": _safe_str(sheet_kanaly.cell_value(r, 15)),
                "rural_district": _safe_str(sheet_kanaly.cell_value(r, 16)),
                "wear_percentage": _safe_float(sheet_kanaly.cell_value(r, 17)),
                "technical_condition": _safe_str(sheet_kanaly.cell_value(r, 18)),
                "cadastral_number": _safe_str(sheet_kanaly.cell_value(r, 19)),
                "state_act": _safe_str(sheet_kanaly.cell_value(r, 20)),
            }

    # Build lookup by row number from 'Лист1' sheet
    list1_lookup = {}
    for r in range(5, sheet_list1.nrows):
        col0 = sheet_list1.cell_value(r, 0)
        if isinstance(col0, float) and 1 <= col0 <= 440:
            list1_lookup[int(col0)] = {
                "structure_count": _convert_cell(sheet_list1.cell_value(r, 17))
                if sheet_list1.cell_value(r, 17)
                else None,
                "year_accepted": _convert_cell(sheet_list1.cell_value(r, 18))
                if sheet_list1.cell_value(r, 18)
                else None,
                "canal_parameters": _safe_str(sheet_list1.cell_value(r, 16)),
            }

    for record in records:
        row_num = record["row_num"]
        kanaly_data = kanaly_lookup.get(row_num, {})
        list1_data = list1_lookup.get(row_num, {})

        # Merge filterable columns — prefer 'каналы', fall back to 'Лист1' (Pitfall #3)
        record["district"] = kanaly_data.get("district")
        record["technical_condition"] = kanaly_data.get("technical_condition")
        record["wear_percentage"] = kanaly_data.get("wear_percentage")
        record["cadastral_number"] = kanaly_data.get("cadastral_number")
        record["rural_district"] = kanaly_data.get("rural_district")
        record["state_act"] = kanaly_data.get("state_act")
        record["structure_count"] = list1_data.get("structure_count")
        record["canal_parameters"] = list1_data.get("canal_parameters")
        record["year_accepted"] = list1_data.get("year_accepted")

    logger.info(
        "enriched_cross_sheet",
        total=len(records),
        with_district=sum(1 for r in records if r.get("district")),
        with_condition=sum(1 for r in records if r.get("technical_condition")),
    )
    return records


def bulk_insert_structures(filepath: str = "датасет.xls", force: bool = False) -> dict:
    """Bulk insert Kazvodhoz spreadsheet records into PostGIS.

    Uses sync psycopg connection for efficient bulk loading (D-17).
    Idempotent: checks source_reference in provenance before inserting (D-19).
    Creates ProvenanceModel + StructureModel + StructureFactModel per record (D-20, D-07).

    Args:
        filepath: Path to the .xls spreadsheet file
        force: If True, re-ingest existing records instead of skipping

    Returns:
        dict with "inserted", "skipped", "total" keys
    """
    engine = create_engine(settings.sync_database_url)

    try:
        wb = xlrd.open_workbook(filepath)
        sheet_korr = wb.sheet_by_name("Корректировка")
        sheet_kanaly = wb.sheet_by_name("каналы")
        sheet_list1 = wb.sheet_by_name("Лист1")

        records = parse_kazvodhoz_sheet(sheet_korr)
        records = enrich_with_cross_sheet_data(records, sheet_kanaly, sheet_list1)

        inserted = 0
        skipped = 0

        with Session(engine) as session:
            for record in records:
                # Idempotency check (D-19)
                source_ref = f"датасет.xls:Корректировка:row:{record['row_num']}"
                existing = session.execute(
                    select(ProvenanceModel).where(
                        ProvenanceModel.source_reference == source_ref
                    )
                ).scalar_one_or_none()

                if existing and not force:
                    skipped += 1
                    continue

                # Create provenance (D-20)
                provenance = ProvenanceModel(
                    source_type="kazvodhoz_spreadsheet",
                    source_reference=source_ref,
                    confidence_level="HIGH",
                    contributor="system:ingestion",
                )
                session.add(provenance)
                session.flush()  # Get provenance.id

                # Create structure with NULL geometry (D-01, D-02) and type='canal' (D-09)
                structure = StructureModel(
                    name_ru=str(record.get("name", "")),
                    type="canal",
                    geometry=None,
                    provenance_id=provenance.id,
                    # Denormalized filterable columns (D-08)
                    district=record.get("district"),
                    water_source=record.get("water_source"),
                    technical_condition=record.get("technical_condition"),
                    wear_percentage=record.get("wear_percentage"),
                    commissioning_year=record.get("commissioning_year"),
                    cadastral_number=record.get("cadastral_number"),
                    structure_count=record.get("structure_count"),
                )
                session.add(structure)
                session.flush()  # Get structure.id

                # Create structure_facts for each spreadsheet column (D-07)
                for attr_name, attr_value in record.get("facts", {}).items():
                    fact = StructureFactModel(
                        structure_id=structure.id,
                        attribute_name=attr_name,
                        attribute_value={"value": attr_value},
                        provenance_id=provenance.id,
                    )
                    session.add(fact)

                inserted += 1

            session.commit()

        logger.info(
            "bulk_insert_complete",
            inserted=inserted,
            skipped=skipped,
            total=len(records),
            force=force,
        )
        return {"inserted": inserted, "skipped": skipped, "total": len(records)}

    finally:
        engine.dispose()
