"""SuJoly Inspector API tools for hydraulic infrastructure data.

These tools query the FastAPI backend for real-time structure data,
risk scores, inspection schedules, and reports.
"""

from typing import Optional

import httpx
import structlog
from langchain_core.tools import tool

from agent.config.settings import settings

logger = structlog.get_logger(__name__)


def _api_get(path: str, **params) -> dict:
    """Make a GET request to the SuJoly API."""
    url = f"{settings.sujoly_api_url}{path}"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("api_get_failed", path=path, error=str(e))
        return {"error": str(e)}


def _format_structure(s: dict) -> str:
    """Format a structure summary for list views."""
    name = s.get("name", "Unnamed")
    obj_type = s.get("type", "?")
    district = s.get("district", "?")
    condition = s.get("technical_condition") or s.get("condition", "?")
    risk_score = s.get("risk_score", "?")
    risk_category = s.get("risk_category", "")
    status = s.get("status", "?")
    obj_id = s.get("id", "?")

    parts = [f"**{name}** (ID: {obj_id})"]
    parts.append(f"  Type: {obj_type}")
    parts.append(f"  District: {district}")
    parts.append(f"  Condition: {condition}")
    parts.append(f"  Risk Score: {risk_score}" + (f" ({risk_category})" if risk_category else ""))
    parts.append(f"  Status: {status}")
    return "\n".join(parts)


@tool
def search_structures(
    query: str,
    district: Optional[str] = None,
    condition: Optional[str] = None,
    risk_status: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Search hydraulic structures (canals, dams, pumps, reservoirs, sluices) in the SuJoly Inspector database.

    Use this for broad searches by name, type, district, condition, or risk status.
    Returns a list of matching structures with key summary fields.

    Args:
        query: Search query (name, type, or keyword).
        district: Filter by district name.
        condition: Filter by technical condition (e.g. 'good', 'satisfactory', 'poor', 'critical').
        risk_status: Filter by risk status/category.
        limit: Maximum number of results to return (default 10).

    Returns:
        Formatted list of matching structures.
    """
    params = {"q": query, "limit": limit}
    if district:
        params["district"] = district
    if condition:
        params["condition"] = condition
    if risk_status:
        params["risk_status"] = risk_status

    result = _api_get("/api/objects", **params)

    if "error" in result:
        return f"Search failed: {result['error']}"

    objects = result.get("objects") or result.get("items") or result
    if isinstance(objects, dict):
        objects = objects.get("items", [])
    if not isinstance(objects, list):
        objects = []

    if not objects:
        return f"No structures found matching '{query}'."

    entries = []
    for i, s in enumerate(objects[:limit], 1):
        entries.append(f"{i}. {_format_structure(s)}")

    header = f"Found {len(objects)} structure(s)"
    if len(objects) > limit:
        header += f" (showing top {limit})"
    header += ":"

    return header + "\n\n" + "\n\n".join(entries)


@tool
def get_structure_details(object_id: str) -> str:
    """Get the full passport (detailed record) for a specific hydraulic structure.

    Use this after search_structures when the user wants complete information about
    one structure: dimensions, capacity, efficiency, condition, risk, coordinates, etc.

    Args:
        object_id: The unique identifier of the structure.

    Returns:
        Full structure passport with all available fields.
    """
    result = _api_get(f"/api/objects/{object_id}")

    if "error" in result:
        return f"Failed to fetch structure details: {result['error']}"

    if not isinstance(result, dict) or not result:
        return f"No structure found with ID '{object_id}'."

    fields = [
        ("name", "Name"),
        ("type", "Type"),
        ("district", "District"),
        ("year_built", "Year Built"),
        ("length_km", "Length (km)"),
        ("capacity", "Capacity"),
        ("design_efficiency", "Design Efficiency"),
        ("actual_efficiency", "Actual Efficiency"),
        ("technical_condition", "Technical Condition"),
        ("wear_percent", "Wear (%)"),
        ("risk_score", "Risk Score"),
        ("risk_category", "Risk Category"),
        ("status", "Status"),
        ("geo_status", "Geo Status"),
        ("coordinates", "Coordinates"),
        ("last_inspection_date", "Last Inspection Date"),
        ("data_quality_flags", "Data Quality Flags"),
    ]

    parts = [f"**Structure Passport — {result.get('name', object_id)}** (ID: {object_id})"]
    for key, label in fields:
        val = result.get(key)
        if val is not None and val != "":
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            parts.append(f"  {label}: {val}")

    # Include any extra fields not explicitly listed
    known_keys = {k for k, _ in fields} | {"id", "name"}
    extras = []
    for k, v in result.items():
        if k not in known_keys and v is not None and v != "":
            if isinstance(v, list):
                v = ", ".join(str(i) for i in v)
            elif isinstance(v, dict):
                v = str(v)
            extras.append(f"  {k}: {v}")
    if extras:
        parts.append("  --- Additional Fields ---")
        parts.extend(extras)

    return "\n".join(parts)


@tool
def get_risk_explanation(object_id: str) -> str:
    """Get the risk score breakdown and explanation for a specific hydraulic structure.

    Use this when the user asks why a structure has a certain risk score or wants to
    understand the factors contributing to the risk assessment.

    Args:
        object_id: The unique identifier of the structure.

    Returns:
        Risk score, category, and component scores with reasons.
    """
    result = _api_get(f"/api/objects/{object_id}/risk")

    if "error" in result:
        return f"Failed to fetch risk explanation: {result['error']}"

    if not isinstance(result, dict) or not result:
        return f"No risk data found for structure '{object_id}'."

    parts = [f"**Risk Breakdown — {result.get('name', object_id)}** (ID: {object_id})"]
    parts.append(f"  Overall Risk Score: {result.get('risk_score', '?')}")
    parts.append(f"  Risk Category: {result.get('risk_category', '?')}")

    components = result.get("components") or result.get("component_scores") or {}
    if isinstance(components, dict) and components:
        parts.append("\n  **Component Scores:**")
        for comp_name, comp_data in components.items():
            if isinstance(comp_data, dict):
                score = comp_data.get("score", "?")
                reason = comp_data.get("reason") or comp_data.get("reasons") or ""
                line = f"    {comp_name}: {score}"
                if reason:
                    line += f" — {reason}"
                parts.append(line)
            else:
                parts.append(f"    {comp_name}: {comp_data}")

    # Known component fields if not nested under 'components'
    flat_components = ["condition", "age", "efficiency", "importance", "weather", "overdue"]
    if not components:
        found = False
        for comp in flat_components:
            val = result.get(comp)
            if val is not None:
                if not found:
                    parts.append("\n  **Component Scores:**")
                    found = True
                if isinstance(val, dict):
                    score = val.get("score", "?")
                    reason = val.get("reason") or val.get("reasons") or ""
                    line = f"    {comp}: {score}"
                    if reason:
                        line += f" — {reason}"
                    parts.append(line)
                else:
                    parts.append(f"    {comp}: {val}")

    return "\n".join(parts)


@tool
def get_inspection_schedule(object_id: str) -> str:
    """Get the recommended inspection interval and next inspection date for a hydraulic structure.

    Use this when the user asks about inspection timing, when the next inspection is due,
    or what priority a structure's inspection has.

    Args:
        object_id: The unique identifier of the structure.

    Returns:
        Next inspection due date, priority, and reasons.
    """
    result = _api_get(f"/api/objects/{object_id}/inspection")

    if "error" in result:
        return f"Failed to fetch inspection schedule: {result['error']}"

    if not isinstance(result, dict) or not result:
        return f"No inspection schedule found for structure '{object_id}'."

    parts = [f"**Inspection Schedule — {result.get('name', object_id)}** (ID: {object_id})"]

    next_due = result.get("next_inspection_date") or result.get("next_due_date") or result.get("due_date")
    if next_due:
        parts.append(f"  Next Inspection Due: {next_due}")

    priority = result.get("priority") or result.get("inspection_priority")
    if priority:
        parts.append(f"  Priority: {priority}")

    interval = result.get("recommended_interval") or result.get("interval_months")
    if interval:
        parts.append(f"  Recommended Interval: {interval}")

    last_inspection = result.get("last_inspection_date")
    if last_inspection:
        parts.append(f"  Last Inspection: {last_inspection}")

    reasons = result.get("reasons") or result.get("reason")
    if reasons:
        if isinstance(reasons, list):
            parts.append("\n  **Reasons:**")
            for r in reasons:
                parts.append(f"    - {r}")
        else:
            parts.append(f"\n  **Reason:** {reasons}")

    return "\n".join(parts)


@tool
def get_top_risk_objects(limit: int = 10, district: Optional[str] = None) -> str:
    """Get the top N riskiest hydraulic structures, ranked by risk score.

    Use this when the user wants to know which structures are most dangerous or
    need urgent attention. Optionally filter by district.

    Args:
        limit: Maximum number of results to return (default 10).
        district: Filter by district name.

    Returns:
        Ranked list of riskiest structures with risk scores and statuses.
    """
    params: dict = {"limit": limit}
    if district:
        params["district"] = district

    result = _api_get("/api/objects/top-risk", **params)

    if "error" in result:
        return f"Failed to fetch top risk objects: {result['error']}"

    objects = result.get("objects") or result.get("items") or result
    if isinstance(objects, dict):
        objects = objects.get("items", [])
    if not isinstance(objects, list):
        objects = []

    if not objects:
        return "No risky structures found."

    entries = []
    for i, s in enumerate(objects[:limit], 1):
        name = s.get("name", "Unnamed")
        obj_id = s.get("id", "?")
        risk_score = s.get("risk_score", "?")
        risk_category = s.get("risk_category", "")
        status = s.get("status", "?")
        district_val = s.get("district", "?")

        line = f"{i}. **{name}** (ID: {obj_id})"
        line += f"\n   Risk Score: {risk_score}" + (f" ({risk_category})" if risk_category else "")
        line += f"\n   District: {district_val} | Status: {status}"
        entries.append(line)

    header = f"**Top {len(objects[:limit])} Riskiest Structures**"
    if district:
        header += f" in {district}"
    header += ":"

    return header + "\n\n" + "\n\n".join(entries)


@tool
def get_objects_without_coordinates(district: Optional[str] = None) -> str:
    """Get hydraulic structures that are missing geolocation (coordinates) data.

    Use this when the user wants to find structures that need geolocation work
    or have incomplete geo data. Optionally filter by district.

    Args:
        district: Filter by district name.

    Returns:
        List of structures missing coordinates.
    """
    params = {}
    if district:
        params["district"] = district

    result = _api_get("/api/objects/missing-geo", **params)

    if "error" in result:
        return f"Failed to fetch objects without coordinates: {result['error']}"

    objects = result.get("objects") or result.get("items") or result
    if isinstance(objects, dict):
        objects = objects.get("items", [])
    if not isinstance(objects, list):
        objects = []

    if not objects:
        return "All structures have coordinates data. No missing geo entries found."

    entries = []
    for i, s in enumerate(objects, 1):
        name = s.get("name", "Unnamed")
        obj_id = s.get("id", "?")
        obj_type = s.get("type", "?")
        district_val = s.get("district", "?")
        entries.append(f"{i}. **{name}** (ID: {obj_id}) — Type: {obj_type}, District: {district_val}")

    header = f"**Structures Missing Coordinates ({len(objects)} found)**:"
    return header + "\n\n" + "\n\n".join(entries)


@tool
def get_district_report(district: str) -> str:
    """Get an aggregate report for a specific district's hydraulic infrastructure.

    Use this when the user wants an overview of a district: total structures,
    condition distribution, risk distribution, top risky structures, and inspection priorities.

    Args:
        district: The district name to report on.

    Returns:
        District summary report with statistics and priorities.
    """
    result = _api_get(f"/api/reports/district/{district}")

    if "error" in result:
        return f"Failed to fetch district report: {result['error']}"

    if not isinstance(result, dict) or not result:
        return f"No report data found for district '{district}'."

    parts = [f"**District Report — {district}**"]

    total = result.get("total_objects") or result.get("total") or result.get("count")
    if total is not None:
        parts.append(f"  Total Objects: {total}")

    condition_dist = result.get("condition_distribution") or result.get("conditions")
    if condition_dist:
        parts.append("\n  **Condition Distribution:**")
        if isinstance(condition_dist, dict):
            for cond, count in condition_dist.items():
                parts.append(f"    {cond}: {count}")
        elif isinstance(condition_dist, list):
            for item in condition_dist:
                if isinstance(item, dict):
                    parts.append(f"    {item.get('condition', '?')}: {item.get('count', '?')}")
                else:
                    parts.append(f"    {item}")

    risk_dist = result.get("risk_distribution") or result.get("risks")
    if risk_dist:
        parts.append("\n  **Risk Distribution:**")
        if isinstance(risk_dist, dict):
            for risk, count in risk_dist.items():
                parts.append(f"    {risk}: {count}")
        elif isinstance(risk_dist, list):
            for item in risk_dist:
                if isinstance(item, dict):
                    parts.append(f"    {item.get('category', item.get('risk', '?'))}: {item.get('count', '?')}")
                else:
                    parts.append(f"    {item}")

    top_risky = result.get("top_risky_objects") or result.get("top_risk") or []
    if top_risky:
        parts.append("\n  **Top Risky Objects:**")
        for item in top_risky[:5]:
            if isinstance(item, dict):
                name = item.get("name", "?")
                score = item.get("risk_score", "?")
                parts.append(f"    - {name} (risk: {score})")
            else:
                parts.append(f"    - {item}")

    inspection_priorities = result.get("inspection_priorities") or result.get("priorities") or []
    if inspection_priorities:
        parts.append("\n  **Inspection Priorities:**")
        for item in inspection_priorities[:5]:
            if isinstance(item, dict):
                name = item.get("name", "?")
                priority = item.get("priority", "?")
                due = item.get("next_inspection_date") or item.get("due_date", "")
                line = f"    - {name} (priority: {priority}"
                if due:
                    line += f", due: {due}"
                line += ")"
                parts.append(line)
            else:
                parts.append(f"    - {item}")

    return "\n".join(parts)


@tool
def get_repair_queue(
    district: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """Get hydraulic structures that need repair, ordered by priority.

    Use this when the user wants to see the repair backlog or which structures
    require maintenance work. Optionally filter by district or repair status.

    Args:
        district: Filter by district name.
        status: Filter by repair status (e.g. 'pending', 'in_progress', 'planned').

    Returns:
        List of structures needing repair with status and reasons.
    """
    params = {"repair_needed": "true"}
    if district:
        params["district"] = district
    if status:
        params["status"] = status

    result = _api_get("/api/objects", **params)

    if "error" in result:
        return f"Failed to fetch repair queue: {result['error']}"

    objects = result.get("objects") or result.get("items") or result
    if isinstance(objects, dict):
        objects = objects.get("items", [])
    if not isinstance(objects, list):
        objects = []

    if not objects:
        return "No structures currently in the repair queue."

    entries = []
    for i, s in enumerate(objects, 1):
        name = s.get("name", "Unnamed")
        obj_id = s.get("id", "?")
        obj_type = s.get("type", "?")
        district_val = s.get("district", "?")
        repair_status = s.get("repair_status") or s.get("status", "?")
        risk_score = s.get("risk_score", "?")
        reason = s.get("repair_reason") or s.get("reason") or ""

        line = f"{i}. **{name}** (ID: {obj_id})"
        line += f"\n   Type: {obj_type} | District: {district_val}"
        line += f"\n   Repair Status: {repair_status} | Risk Score: {risk_score}"
        if reason:
            line += f"\n   Reason: {reason}"
        entries.append(line)

    header = f"**Repair Queue ({len(objects)} structures needing repair)**:"
    return header + "\n\n" + "\n\n".join(entries)
