"""OSM Overpass discovery service — async hydraulic structure candidate discovery.

Provides:
- discover_from_osm: query OSM Overpass API for hydraulic structures in a bbox
- discover_candidates: run discovery and persist candidates to DB with dedup

Uses httpx.AsyncClient for async HTTP calls to the Overpass API.
Default tags target hydraulic structures: waterway=canal/dam/weir/sluice,
man_made=water_works.
"""

import uuid
from datetime import datetime, timezone

import httpx
import structlog

from api.infrastructure.database import async_session
from api.models.candidate import CandidateModel
from api.models.provenance import ProvenanceModel
from api.schemas.candidates import CandidateCreate
from sqlalchemy import select

logger = structlog.get_logger(__name__)

# Default OSM tags for hydraulic structure discovery
_DEFAULT_OSM_TAGS = [
    "waterway=canal",
    "waterway=dam",
    "waterway=weir",
    "waterway=sluice_gate",
    "man_made=water_works",
    "man_made=dam",
    "waterway=lock_gate",
    "natural=water+water=reservoir",
]

_OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"


def _build_overpass_query(bbox: str, tags: list[str] | None = None) -> str:
    """Build Overpass QL query for hydraulic structures in bbox.

    Args:
        bbox: "south,west,north,east" format (Overpass bbox order).
        tags: OSM tag filters, defaults to _DEFAULT_OSM_TAGS.

    Returns:
        Overpass QL query string.
    """
    tag_list = tags or _DEFAULT_OSM_TAGS
    # Overpass bbox order: south,west,north,east
    # API input bbox format: "minx,miny,maxx,maxy" = west,south,east,north
    parts = bbox.split(",")
    if len(parts) != 4:
        raise ValueError("bbox must contain exactly 4 values: minx,miny,maxx,maxy")
    minx, miny, maxx, maxy = (float(p) for p in parts)
    overpass_bbox = f"{miny},{minx},{maxy},{maxx}"

    # Build union of queries for each tag
    queries = []
    for tag in tag_list:
        if "+" in tag:
            # Compound tag like "natural=water+water=reservoir"
            parts_tag = tag.split("+")
            tag_parts = []
            for pt in parts_tag:
                k, v = pt.split("=", 1)
                tag_parts.append(f'["{k}"="{v}"]')
            query = f"  node{"".join(tag_parts)}({overpass_bbox});\n  way{"".join(tag_parts)}({overpass_bbox});\n"
        else:
            k, v = tag.split("=", 1)
            query = f'  node["{k}"="{v}"]({overpass_bbox});\n  way["{k}"="{v}"]({overpass_bbox});\n'
        queries.append(query)

    overpass_query = (
        "[out:json][timeout:60];\n"
        "(\n"
        + "".join(queries)
        + ");\n"
        "out center;\n"
    )
    return overpass_query


def _parse_osm_element(element: dict) -> CandidateCreate | None:
    """Parse a single OSM element from Overpass response into CandidateCreate.

    Extracts name, coordinates, tags as evidence, and inferred type.
    Returns None if element has no tags or no useful data.

    Args:
        element: OSM element dict with type, id, lat/lon or center, tags.

    Returns:
        CandidateCreate or None if element is not usable.
    """
    tags = element.get("tags", {})
    if not tags:
        return None

    name = tags.get("name") or tags.get("name:ru") or tags.get("name:en") or tags.get("name:kk")
    if not name:
        # Skip unnamed elements — they cannot be meaningfully matched by name
        return None

    # Get coordinates — ways have center from "out center;"
    lat = element.get("lat") or element.get("center", {}).get("lat")
    lon = element.get("lon") or element.get("center", {}).get("lon")

    # Build source_id from OSM type + id
    osm_type = element.get("type", "node")
    osm_id = element.get("id", "")
    source_id = f"{osm_type}/{osm_id}"

    # Infer structure type from OSM tags
    inferred_type = None
    if tags.get("waterway") in ("dam", "weir", "sluice_gate", "lock_gate"):
        inferred_type = tags["waterway"]
    elif tags.get("man_made") == "dam":
        inferred_type = "dam"
    elif tags.get("waterway") == "canal":
        inferred_type = "canal"
    elif tags.get("man_made") == "water_works":
        inferred_type = "water_works"

    return CandidateCreate(
        source_type="osm",
        source_id=source_id,
        name=name,
        latitude=lat,
        longitude=lon,
        evidence={"osm": {"tags": tags, "element_type": osm_type}},
        district=None,
        water_source=tags.get("waterway:name") or tags.get("river"),
        type=inferred_type,
    )


class DiscoveryService:
    """Service for discovering hydraulic structure candidates from external sources.

    Currently supports OSM Overpass API. Designed for extension to satellite,
    OCR, and other sources.
    """

    async def discover_from_osm(
        self, bbox: str, tags: list[str] | None = None
    ) -> list[CandidateCreate]:
        """Query OSM Overpass API for hydraulic structures in bbox.

        Args:
            bbox: Bounding box in "minx,miny,maxx,maxy" format (EPSG:4326).
            tags: OSM tag filters, defaults to hydraulic structure tags.

        Returns:
            List of CandidateCreate schemas ready for insertion.
        """
        query = _build_overpass_query(bbox, tags)
        logger.info("overpass_query_start", bbox=bbox)

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                _OVERPASS_API_URL,
                data={"data": query},
            )
            response.raise_for_status()
            data = response.json()

        elements = data.get("elements", [])
        candidates = []
        for element in elements:
            candidate = _parse_osm_element(element)
            if candidate is not None:
                candidates.append(candidate)

        logger.info(
            "overpass_query_complete",
            total_elements=len(elements),
            candidates_parsed=len(candidates),
        )
        return candidates

    async def discover_candidates(
        self, bbox: str, source: str = "osm"
    ) -> list[CandidateModel]:
        """Run discovery and persist candidates to DB with dedup.

        1. Call discover_from_osm (or other sources later)
        2. For each candidate, check if source_id already exists (dedup)
        3. Insert new candidates with provenance
        4. Return created candidates

        Args:
            bbox: Bounding box in "minx,miny,maxx,maxy" format.
            source: Discovery source (currently only "osm" supported).

        Returns:
            List of created CandidateModel instances.
        """
        if source != "osm":
            raise ValueError(f"Unsupported discovery source: {source}. Only 'osm' is supported.")

        candidates_data = await self.discover_from_osm(bbox)

        created = []
        async with async_session() as session:
            async with session.begin():
                for candidate_data in candidates_data:
                    # Dedup: check if source_id already exists
                    existing = await session.execute(
                        select(CandidateModel).where(
                            CandidateModel.source_id == candidate_data.source_id,
                            CandidateModel.source_type == "osm",
                        )
                    )
                    if existing.scalar_one_or_none() is not None:
                        logger.debug(
                            "candidate_dedup_skip",
                            source_id=candidate_data.source_id,
                        )
                        continue

                    # Create provenance record
                    provenance = ProvenanceModel(
                        source_type="osm",
                        source_reference=f"osm:{candidate_data.source_id}",
                        confidence_level="MEDIUM",
                        contributor="overpass_api",
                    )
                    session.add(provenance)
                    await session.flush()

                    # Create geometry WKT if lat/lng available
                    geometry_wkt = None
                    if candidate_data.latitude is not None and candidate_data.longitude is not None:
                        geometry_wkt = (
                            f"SRID=4326;POINT({candidate_data.longitude} {candidate_data.latitude})"
                        )

                    # Create candidate model
                    model = CandidateModel(
                        name=candidate_data.name,
                        source_type=candidate_data.source_type,
                        source_id=candidate_data.source_id,
                        geometry=geometry_wkt,
                        match_status="unmatched",
                        confidence="MEDIUM",
                        evidence=candidate_data.evidence,
                        district=candidate_data.district,
                        water_source=candidate_data.water_source,
                        type=candidate_data.type,
                        provenance_id=provenance.id,
                    )
                    session.add(model)
                    await session.flush()
                    await session.refresh(model)
                    created.append(model)

        logger.info(
            "discovery_complete",
            total_parsed=len(candidates_data),
            new_created=len(created),
        )
        return created
