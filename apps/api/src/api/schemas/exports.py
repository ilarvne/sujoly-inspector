"""Pydantic schemas for export endpoints (D-19).

Provides:
- ExportParams: query parameter validation for structure export endpoints
"""

from typing import Literal

from pydantic import BaseModel


class ExportParams(BaseModel):
    """Query parameters for structure export endpoints (D-19).

    Supports:
    - format: csv or geojson output
    - lang: trilingual output (ru/kk/en) per D-23
    - type, district, condition, bbox: filter params to scope the export
    """

    format: Literal["csv", "geojson"] = "csv"
    lang: Literal["ru", "kk", "en"] = "ru"
    type: str | None = None
    district: str | None = None
    condition: str | None = None
    bbox: str | None = None
