"""Tests for Kazvodhoz spreadsheet ingestion pipeline.

Tests cover:
- parse_kazvodhoz_sheet: row parsing, cell type handling, header/summary row skipping
- enrich_with_cross_sheet_data: cross-sheet enrichment from 'каналы' and 'Лист1'
- bulk_insert_structures: idempotent ingestion, provenance creation, force reingest
- API endpoints: POST /ingestion/kazvodhoz (202 + job_id), GET status

TDD RED phase: these tests fail because ingestion_service.py does not exist yet.
"""

import tempfile
from unittest.mock import MagicMock, patch

import pytest


class TestIngestionParsing:
    """Tests for parse_kazvodhoz_sheet — xlrd sheet parsing logic."""

    def _mock_sheet(self, rows):
        """Create a MagicMock simulating an xlrd Sheet.

        Args:
            rows: list of lists — each inner list is a row's cell values.
                  Col 0 is the row number (float for data rows, str for headers).

        Returns:
            MagicMock with cell_value(row, col), nrows, ncols attributes.
        """
        sheet = MagicMock()
        sheet.nrows = len(rows)
        sheet.ncols = max(len(r) for r in rows) if rows else 0

        def cell_value(row_idx, col_idx):
            if row_idx < 0 or row_idx >= len(rows):
                return ""
            row = rows[row_idx]
            if col_idx < 0 or col_idx >= len(row):
                return ""
            return row[col_idx]

        sheet.cell_value = cell_value
        return sheet

    def test_parse_kazvodhoz_sheet(self):
        """parse_kazvodhoz_sheet returns list of dicts with row_num, name, commissioning_year, water_source.
        Skips rows where col0 is not a float in range [1, 440].
        """
        from api.services.ingestion_service import parse_kazvodhoz_sheet

        # Simulate sheet: headers (rows 0-6), then data rows starting at row 7
        rows = (
            [["Title"] * 13] * 5  # rows 0-4: multi-row headers
            + [["sub-header"] * 13]  # row 5
            + [[1.0, 2.0, 3.0] + [""] * 10]  # row 6: column numbers
            + [[1.0, "Канал 1", 1973.0, "р. Иртыш", 2.5, 10.0, 5.0, 3.0, "", 8.0, "", "", "", "note"]]
            + [[2.0, "Канал 2", 1985.0, "р. Нура", 1.8, 15.0, 8.0, 5.0, "", 12.0, "", "", "", ""]]
        )
        sheet = self._mock_sheet(rows)
        records = parse_kazvodhoz_sheet(sheet)

        assert isinstance(records, list)
        assert len(records) == 2
        assert records[0]["row_num"] == 1
        assert records[0]["name"] == "Канал 1"
        assert records[1]["row_num"] == 2
        assert records[1]["name"] == "Канал 2"

    def test_cell_type_handling(self):
        """float cell value 1973.0 for commissioning_year is converted to int 1973."""
        from api.services.ingestion_service import parse_kazvodhoz_sheet

        rows = (
            [[""] * 13] * 7  # 7 header rows
            + [[1.0, "Канал 1", 1973.0, "р. Иртыш", 2.5, 10.0, 5.0, 3.0, "", 8.0, "", "", "", ""]]
        )
        sheet = self._mock_sheet(rows)
        records = parse_kazvodhoz_sheet(sheet)

        assert len(records) == 1
        assert records[0]["commissioning_year"] == 1973
        assert isinstance(records[0]["commissioning_year"], int)
        assert not isinstance(records[0]["commissioning_year"], float)

    def test_skip_group_headers(self):
        """rows with col0='Категория объектов' (string) are skipped, not included in records."""
        from api.services.ingestion_service import parse_kazvodhoz_sheet

        rows = (
            [[""] * 13] * 7  # 7 header rows
            + [["Категория объектов", "", "", "", "", "", "", "", "", "", "", "", ""]]
            + [["Группа объектов 1", "", "", "", "", "", "", "", "", "", "", "", ""]]
            + [[1.0, "Канал 1", 1973.0, "р. Иртыш", 2.5, 10.0, 5.0, 3.0, "", 8.0, "", "", "", ""]]
            + [["Группа объектов 2", "", "", "", "", "", "", "", "", "", "", "", ""]]
            + [[2.0, "Канал 2", 1985.0, "р. Нура", 1.8, 15.0, 8.0, 5.0, "", 12.0, "", "", "", ""]]
        )
        sheet = self._mock_sheet(rows)
        records = parse_kazvodhoz_sheet(sheet)

        assert len(records) == 2
        assert all(r["row_num"] in (1, 2) for r in records)
        # No group header text in names
        assert all("Категория" not in (r.get("name") or "") for r in records)
        assert all("Группа" not in (r.get("name") or "") for r in records)

    def test_skip_summary_rows(self):
        """rows with col0 > 440 or empty col1 are skipped."""
        from api.services.ingestion_service import parse_kazvodhoz_sheet

        rows = (
            [[""] * 13] * 7  # 7 header rows
            + [[1.0, "Канал 1", 1973.0, "р. Иртыш", 2.5, 10.0, 5.0, 3.0, "", 8.0, "", "", "", ""]]
            # Summary rows: col0 > 440
            + [[441.0, "", "", "", "", "", "", "", "", "", "", "", ""]]
            + [[442.0, "Итого", "", "", "", 833.33, "", "", "", "", "", "", "", ""]]
            # Row with col0 in range but empty col1 (name)
            + [[3.0, "", 1990.0, "р. Талас", 1.0, 5.0, 2.0, 1.0, "", 4.0, "", "", "", ""]]
        )
        sheet = self._mock_sheet(rows)
        records = parse_kazvodhoz_sheet(sheet)

        # Only row 1 should be in records (row 3 skipped due to empty name,
        # rows 441/442 skipped due to col0 > 440)
        assert len(records) == 1
        assert records[0]["row_num"] == 1


class TestIngestionIdempotency:
    """Tests for bulk_insert_structures idempotency (D-19)."""

    def test_idempotent_skip(self):
        """bulk_insert_structures with existing source_reference skips the record when force=False."""
        from api.services.ingestion_service import bulk_insert_structures

        # Mock the database session and query to simulate existing provenance
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # existing provenance
        mock_session.execute.return_value = mock_result

        mock_engine = MagicMock()
        mock_session_cm = MagicMock()
        mock_session_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cm.__exit__ = MagicMock(return_value=None)

        with (
            patch("api.services.ingestion_service.create_engine", return_value=mock_engine),
            patch("api.services.ingestion_service.Session", return_value=mock_session_cm),
            patch("api.services.ingestion_service.xlrd") as mock_xlrd,
        ):
            # Mock xlrd to return a sheet with 1 data row
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.nrows = 8
            mock_sheet.ncols = 13
            mock_sheet.cell_value = MagicMock(
                side_effect=lambda r, c: {7: {0: 1.0, 1: "Канал 1"}}.get(r, {}).get(c, "")
            )
            mock_wb.sheet_by_name.return_value = mock_sheet
            mock_xlrd.open_workbook.return_value = mock_wb

            result = bulk_insert_structures("test.xls", force=False)

        assert result["inserted"] == 0
        assert result["skipped"] == 1

    def test_force_reingest(self):
        """bulk_insert_structures with force=True re-ingests existing records."""
        from api.services.ingestion_service import bulk_insert_structures

        # Mock the database session — existing provenance found but force=True
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # existing provenance
        mock_session.execute.return_value = mock_result

        mock_engine = MagicMock()
        mock_session_cm = MagicMock()
        mock_session_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cm.__exit__ = MagicMock(return_value=None)

        with (
            patch("api.services.ingestion_service.create_engine", return_value=mock_engine),
            patch("api.services.ingestion_service.Session", return_value=mock_session_cm),
            patch("api.services.ingestion_service.xlrd") as mock_xlrd,
        ):
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.nrows = 8
            mock_sheet.ncols = 13
            mock_sheet.cell_value = MagicMock(
                side_effect=lambda r, c: {7: {0: 1.0, 1: "Канал 1"}}.get(r, {}).get(c, "")
            )
            mock_wb.sheet_by_name.return_value = mock_sheet
            mock_xlrd.open_workbook.return_value = mock_wb

            result = bulk_insert_structures("test.xls", force=True)

        # With force=True, should insert despite existing provenance
        assert result["inserted"] == 1
        assert result["skipped"] == 0


class TestIngestionProvenance:
    """Tests for provenance creation during ingestion (D-20)."""

    def test_provenance_creation(self):
        """each inserted structure gets a ProvenanceModel with source_type='kazvodhoz_spreadsheet',
        confidence_level='HIGH', contributor='system:ingestion'.
        """
        from api.services.ingestion_service import bulk_insert_structures

        mock_session = MagicMock()
        # No existing provenance — simulate new insert
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Track objects added to session
        added_objects = []
        mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
        mock_session.flush = MagicMock()
        mock_session.commit = MagicMock()

        mock_engine = MagicMock()
        mock_session_cm = MagicMock()
        mock_session_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cm.__exit__ = MagicMock(return_value=None)

        with (
            patch("api.services.ingestion_service.create_engine", return_value=mock_engine),
            patch("api.services.ingestion_service.Session", return_value=mock_session_cm),
            patch("api.services.ingestion_service.xlrd") as mock_xlrd,
        ):
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.nrows = 8
            mock_sheet.ncols = 13
            mock_sheet.cell_value = MagicMock(
                side_effect=lambda r, c: {7: {0: 1.0, 1: "Канал 1"}}.get(r, {}).get(c, "")
            )
            mock_wb.sheet_by_name.return_value = mock_sheet
            mock_xlrd.open_workbook.return_value = mock_wb

            result = bulk_insert_structures("test.xls", force=False)

        # Check that ProvenanceModel was created with correct fields
        provenance_models = [
            obj for obj in added_objects if hasattr(obj, "source_type") and hasattr(obj, "confidence_level")
        ]
        assert len(provenance_models) >= 1
        prov = provenance_models[0]
        assert prov.source_type == "kazvodhoz_spreadsheet"
        assert prov.confidence_level == "HIGH"
        assert prov.contributor == "system:ingestion"

        # Verify result
        assert result["inserted"] == 1
