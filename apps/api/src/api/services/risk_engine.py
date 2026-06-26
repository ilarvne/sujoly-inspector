"""Risk computation engine — pure Python module (D-01).

Computes risk-informed inspection intervals and repair priorities for hydraulic
structures using a semi-quantitative formula (D-02/D-03) with red-flag overrides
(D-07), four repair statuses (D-08), and a weak-evidence floor (D-09).

This module is intentionally pure: no database imports, no async, no side effects.
It takes structure data as plain dicts and returns a RiskAssessment dataclass
with a full factor breakdown for explainability.

Formula (D-02/D-03):
    composite_score = condition_score * consequence_factor
                      * seasonal_modifier * staleness_modifier

Architecture principle (PROJECT.md):
    "Semi-quantitative risk index over black-box ML" — defensible, explainable.
    "LLMs never make final engineering decisions."
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class RiskAssessment:
    """Result of a risk computation with full factor breakdown (D-04).

    Fields:
        condition_score: Blended 0-100 score (0=perfect, 100=total failure) per D-06.
        consequence_factor: Structure-type-based factor (0.5-2.0) per D-02.
        seasonal_modifier: Flood-season urgency multiplier (0.8-1.5) per D-02.
        staleness_modifier: Data-freshness multiplier (0.5-1.5) per D-02.
        composite_score: condition_score * consequence * seasonal * staleness per D-03.
        inspection_interval: One of emergency/30d/90d/180d/12mo/24mo per D-03.
        repair_status: One of normal/inspection_required/repair_required/critical_condition per D-08.
        red_flags: Triggered red-flag identifiers per D-07.
        contributing_factors: Dict of input values that fed the computation.
        weak_evidence_reasons: List of weak-evidence triggers per D-09.
    """

    condition_score: float
    consequence_factor: float
    seasonal_modifier: float
    staleness_modifier: float
    composite_score: float
    inspection_interval: str
    repair_status: str
    red_flags: list[str] = field(default_factory=list)
    contributing_factors: dict[str, Any] = field(default_factory=dict)
    weak_evidence_reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# D-02: Condition score mapping for Russian technical_condition text
# ---------------------------------------------------------------------------

_CONDITION_MAP: dict[str, int] = {
    "хорошее": 90,
    "удовлетворительное": 60,
    "неудовлетворительное": 30,
    "аварийное": 10,
}

# ---------------------------------------------------------------------------
# D-02: Consequence factor by structure type
# ---------------------------------------------------------------------------

_CONSEQUENCE_BY_TYPE: dict[str, float] = {
    "dam": 2.0,
    "weir": 2.0,
    "reservoir": 1.8,
    "canal": 1.0,
    "pipeline": 1.2,
    "pumping_station": 1.5,
}

# ---------------------------------------------------------------------------
# D-07: Red-flag keywords (Russian inspection findings)
# ---------------------------------------------------------------------------

_REDFLAG_KEYWORDS: list[str] = [
    "просачивание",
    "деформация",
    "эрозия",
    "быстрая эрозия",
    "аварийная ситуация",
    "повторные аварийные ситуации",
]


# ---------------------------------------------------------------------------
# D-02: Seasonal modifier — Kazakhstan flood season
# ---------------------------------------------------------------------------


def _seasonal_modifier(assessment_date: date) -> float:
    """Return seasonal urgency multiplier based on month (D-02).

    March-May (flood season) -> 1.5
    January-February (pre-flood) -> 1.2
    All other months (dry season) -> 0.8
    """
    month = assessment_date.month
    if 3 <= month <= 5:  # Flood season (March-May)
        return 1.5
    elif month in (1, 2):  # Pre-flood inspection period
        return 1.2
    else:  # Dry season
        return 0.8


# ---------------------------------------------------------------------------
# D-02: Staleness modifier — data freshness
# ---------------------------------------------------------------------------


def _staleness_modifier(days_since_inspection: int | None) -> float:
    """Return staleness multiplier based on days since last inspection (D-02).

    None (never inspected) -> 1.5
    <90 days (fresh)       -> 0.5
    90-179 days            -> 0.8
    180-364 days           -> 1.0
    365-729 days           -> 1.2
    >=730 days (stale)     -> 1.5
    """
    if days_since_inspection is None:
        return 1.5  # Never inspected
    if days_since_inspection < 90:
        return 0.5
    elif days_since_inspection < 180:
        return 0.8
    elif days_since_inspection < 365:
        return 1.0
    elif days_since_inspection < 730:
        return 1.2
    else:
        return 1.5


# ---------------------------------------------------------------------------
# D-06: Blended condition score
# ---------------------------------------------------------------------------


def compute_condition_score(
    wear_percentage: float | None,
    technical_condition: str | None,
    last_inspection_score: float | None,
) -> float:
    """Compute blended condition score (0-100) per D-06.

    0 = perfect condition, 100 = total failure.

    Weights: wear 40%, technical_condition text 40%, last inspection 20%.
    Weights are redistributed proportionally when components are missing.
    Returns 50.0 (default) when no data is available.
    """
    # wear_score: invert wear (high wear = low score)
    wear_score = (100 - wear_percentage) if wear_percentage is not None else None

    # condition_score from Russian text mapping
    condition_score = _CONDITION_MAP.get(
        technical_condition.lower() if technical_condition else "", None
    )

    inspection_score = last_inspection_score

    # Build list of (name, value, weight) for available components
    components: list[tuple[str, float, float]] = []
    if wear_score is not None:
        components.append(("wear", wear_score, 0.4))
    if condition_score is not None:
        components.append(("condition", condition_score, 0.4))
    if inspection_score is not None:
        components.append(("inspection", inspection_score, 0.2))

    if not components:
        return 50.0  # Default when no data available

    # Redistribute weights proportionally (D-02)
    total_weight = sum(w for _, _, w in components)
    score = sum(val * (w / total_weight) for _, val, w in components)

    # Clamp to 0-100 (D-06)
    return min(100.0, max(0.0, score))


# ---------------------------------------------------------------------------
# D-07: Red-flag detection
# ---------------------------------------------------------------------------


def detect_red_flags(
    wear_percentage: float | None,
    technical_condition: str | None,
    inspection_findings: str | None,
    structure_facts: dict | None,
) -> list[str]:
    """Detect red-flag conditions per D-07.

    Triggers:
    - wear_percentage >= 80 -> "wear_percentage_ge_80"
    - technical_condition == "аварийное" -> "emergency_condition"
    - Keyword match in findings/facts text -> "keyword:{keyword}"

    Returns list of triggered red-flag identifiers (may be empty).
    """
    flags: list[str] = []

    # Wear percentage check
    if wear_percentage is not None and wear_percentage >= 80:
        flags.append("wear_percentage_ge_80")

    # Emergency condition check
    if technical_condition and technical_condition.lower() == "аварийное":
        flags.append("emergency_condition")

    # Keyword search in findings + facts text (case-insensitive)
    text_to_scan = " ".join(
        filter(
            None,
            [
                inspection_findings or "",
                " ".join(str(v) for v in (structure_facts or {}).values()),
            ],
        )
    ).lower()

    for keyword in _REDFLAG_KEYWORDS:
        if keyword in text_to_scan:
            flags.append(f"keyword:{keyword}")

    return flags


# ---------------------------------------------------------------------------
# D-01/D-02/D-03: Main risk computation entry point
# ---------------------------------------------------------------------------


def compute_risk(
    structure: dict,
    facts: list[dict],
    inspections: list[dict],
    assessment_date: date | None = None,
) -> RiskAssessment:
    """Compute a risk assessment for a hydraulic structure (D-01/D-02/D-03).

    Args:
        structure: Dict with keys like wear_percentage, technical_condition, type.
        facts: List of fact dicts with attribute_name and attribute_value keys.
        inspections: List of inspection dicts (newest first) with inspection_date,
            findings, condition_score_at_inspection.
        assessment_date: Date of assessment (defaults to today).

    Returns:
        RiskAssessment with full factor breakdown for explainability.
    """
    assessment_date = assessment_date or date.today()

    # --- Extract structure inputs ---
    wear = structure.get("wear_percentage")
    condition_text = structure.get("technical_condition")

    # --- Last inspection (inspections[0] is most recent) ---
    last_inspection = inspections[0] if inspections else None
    last_inspection_score = (
        last_inspection.get("condition_score_at_inspection") if last_inspection else None
    )

    # --- D-06: Condition score ---
    condition_score = compute_condition_score(wear, condition_text, last_inspection_score)

    # --- D-02: Consequence factor ---
    consequence = _CONSEQUENCE_BY_TYPE.get(structure.get("type", ""), 1.0)

    # --- D-02: Seasonal modifier ---
    seasonal = _seasonal_modifier(assessment_date)

    # --- D-02: Staleness modifier ---
    days_since: int | None = None
    if last_inspection and last_inspection.get("inspection_date"):
        days_since = (assessment_date - last_inspection["inspection_date"]).days

    staleness = _staleness_modifier(days_since)

    # --- D-07: Red flags ---
    # Build a flat dict of facts for keyword scanning
    facts_dict = {f["attribute_name"]: f["attribute_value"] for f in facts} if facts else {}
    red_flags = detect_red_flags(
        wear,
        condition_text,
        last_inspection.get("findings") if last_inspection else None,
        facts_dict,
    )

    # --- D-02/D-03: Composite score ---
    composite = condition_score * consequence * seasonal * staleness

    # --- D-03: Map composite to inspection interval via threshold bands ---
    if composite >= 200 or red_flags:
        interval = "emergency"
    elif composite >= 150:
        interval = "30d"
    elif composite >= 100:
        interval = "90d"
    elif composite >= 60:
        interval = "180d"
    elif composite >= 30:
        interval = "12mo"
    else:
        interval = "24mo"

    # --- D-08: Map blended condition score to repair status ---
    if condition_score >= 90 or red_flags:
        status_val = "critical_condition"
    elif condition_score >= 70:
        status_val = "repair_required"
    elif condition_score >= 40:
        status_val = "inspection_required"
    else:
        status_val = "normal"

    # --- D-09: Weak evidence floor ---
    weak_evidence: list[str] = []
    if structure.get("provenance_confidence") == "LOW":
        weak_evidence.append("low_confidence_provenance")
    if not inspections:
        weak_evidence.append("never_inspected")
    elif days_since and days_since > 730:  # > 24 months
        weak_evidence.append("stale_inspection_24mo")

    # Floor: if weak evidence and status is "normal", bump to "inspection_required"
    if weak_evidence and status_val == "normal":
        status_val = "inspection_required"

    # --- Assemble result ---
    return RiskAssessment(
        condition_score=condition_score,
        consequence_factor=consequence,
        seasonal_modifier=seasonal,
        staleness_modifier=staleness,
        composite_score=composite,
        inspection_interval=interval,
        repair_status=status_val,
        red_flags=red_flags,
        contributing_factors={
            "wear_percentage": wear,
            "technical_condition": condition_text,
            "structure_type": structure.get("type"),
            "days_since_last_inspection": days_since,
            "last_inspection_score": last_inspection_score,
        },
        weak_evidence_reasons=weak_evidence,
    )
