"""Tests for risk engine computation module (RISK-01 through RISK-05).

Covers:
- compute_condition_score blending with weight redistribution (D-06)
- Seasonal modifier for Kazakhstan flood season (D-02)
- Staleness modifier for data freshness (D-02)
- Composite risk score = condition x consequence x seasonal x staleness (D-02/D-03)
- Inspection interval mapping via threshold bands (D-03)
- Red-flag detection and overrides (D-07)
- Repair status determination via blended score (D-08)
- Weak-evidence floor preventing false certainty (D-09)
- RiskAssessment dataclass field completeness (D-04)
"""

from dataclasses import fields as dataclass_fields
from datetime import date, timedelta

import pytest

from api.services.risk_engine import (
    RiskAssessment,
    compute_condition_score,
    compute_risk,
    detect_red_flags,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _inspection(days_ago: int, assessment: date, **overrides) -> dict:
    """Create an inspection dict dated *days_ago* before *assessment*."""
    insp = {
        "inspection_date": assessment - timedelta(days=days_ago),
        "findings": "",
        "condition_score_at_inspection": None,
    }
    insp.update(overrides)
    return insp


# ---------------------------------------------------------------------------
# D-06: Condition score blending
# ---------------------------------------------------------------------------


class TestConditionScore:
    """Tests for compute_condition_score blending logic (D-06)."""

    def test_compute_condition_score_blend(self):
        """wear=40 (score=60), condition text score=60, inspection=50 -> 58.0."""
        result = compute_condition_score(40, "\u0443\u0434\u043e\u0432\u043b\u0435\u0442\u0432\u043e\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435", 50)
        assert result == pytest.approx(58.0)

    def test_compute_condition_score_weight_redistribution(self):
        """Only wear=40 available -> score=60.0 (100-40, 100% weight on wear)."""
        result = compute_condition_score(40, None, None)
        assert result == pytest.approx(60.0)

    def test_compute_condition_score_no_data(self):
        """All inputs None -> score=50.0 (default)."""
        result = compute_condition_score(None, None, None)
        assert result == pytest.approx(50.0)

    def test_compute_condition_score_avarialnoe(self):
        """technical_condition='аварийное' -> score contribution = 10."""
        result = compute_condition_score(None, "\u0430\u0432\u0430\u0440\u0438\u0439\u043d\u043e\u0435", None)
        assert result == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# D-02: Seasonal modifier
# ---------------------------------------------------------------------------


class TestSeasonalModifier:
    """Tests for seasonal modifier (D-02)."""

    def test_seasonal_modifier_flood_season(self):
        """March, April, May -> 1.5 (flood season)."""
        for test_date in [date(2026, 3, 15), date(2026, 4, 15), date(2026, 5, 15)]:
            result = compute_risk(
                structure={"type": "canal"},
                facts=[],
                inspections=[],
                assessment_date=test_date,
            )
            assert result.seasonal_modifier == 1.5

    def test_seasonal_modifier_pre_flood(self):
        """January, February -> 1.2 (pre-flood)."""
        for test_date in [date(2026, 1, 15), date(2026, 2, 15)]:
            result = compute_risk(
                structure={"type": "canal"},
                facts=[],
                inspections=[],
                assessment_date=test_date,
            )
            assert result.seasonal_modifier == 1.2

    def test_seasonal_modifier_dry_season(self):
        """June, December -> 0.8 (dry season)."""
        for test_date in [date(2026, 6, 15), date(2026, 12, 15)]:
            result = compute_risk(
                structure={"type": "canal"},
                facts=[],
                inspections=[],
                assessment_date=test_date,
            )
            assert result.seasonal_modifier == 0.8


# ---------------------------------------------------------------------------
# D-02: Staleness modifier
# ---------------------------------------------------------------------------


class TestStalenessModifier:
    """Tests for staleness modifier (D-02)."""

    def test_staleness_modifier_never_inspected(self):
        """days_since=None -> 1.5 (never inspected)."""
        result = compute_risk(
            structure={"type": "canal"},
            facts=[],
            inspections=[],
            assessment_date=date(2026, 6, 15),
        )
        assert result.staleness_modifier == 1.5

    def test_staleness_modifier_fresh(self):
        """days_since=45 -> 0.5 (<90 days, fresh)."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal"},
            facts=[],
            inspections=[_inspection(45, assessment)],
            assessment_date=assessment,
        )
        assert result.staleness_modifier == 0.5

    def test_staleness_modifier_90_180(self):
        """days_since=120 -> 0.8 (90-180 days)."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal"},
            facts=[],
            inspections=[_inspection(120, assessment)],
            assessment_date=assessment,
        )
        assert result.staleness_modifier == 0.8

    def test_staleness_modifier_180_365(self):
        """days_since=200 -> 1.0 (180-365 days)."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal"},
            facts=[],
            inspections=[_inspection(200, assessment)],
            assessment_date=assessment,
        )
        assert result.staleness_modifier == 1.0

    def test_staleness_modifier_365_730(self):
        """days_since=400 -> 1.2 (365-730 days)."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal"},
            facts=[],
            inspections=[_inspection(400, assessment)],
            assessment_date=assessment,
        )
        assert result.staleness_modifier == 1.2

    def test_staleness_modifier_over_730(self):
        """days_since=800 -> 1.5 (>730 days, very stale)."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal"},
            facts=[],
            inspections=[_inspection(800, assessment)],
            assessment_date=assessment,
        )
        assert result.staleness_modifier == 1.5


# ---------------------------------------------------------------------------
# D-02/D-03: Composite score
# ---------------------------------------------------------------------------


class TestCompositeScore:
    """Tests for composite risk score calculation (D-02/D-03)."""

    def test_compute_risk_composite_score(self):
        """condition=60, consequence=2.0 (dam), seasonal=1.5 (March), staleness=1.0 -> 180.0."""
        assessment = date(2026, 3, 15)
        result = compute_risk(
            structure={"type": "dam", "wear_percentage": 40},
            facts=[],
            inspections=[_inspection(181, assessment)],
            assessment_date=assessment,
        )
        # condition_score = 100-40 = 60 (only wear, 100% weight)
        # consequence = 2.0 (dam)
        # seasonal = 1.5 (March)
        # staleness = 1.0 (181 days, in 180-365 range)
        assert result.condition_score == pytest.approx(60.0)
        assert result.consequence_factor == pytest.approx(2.0)
        assert result.seasonal_modifier == pytest.approx(1.5)
        assert result.staleness_modifier == pytest.approx(1.0)
        assert result.composite_score == pytest.approx(180.0)


# ---------------------------------------------------------------------------
# D-03: Inspection interval mapping
# ---------------------------------------------------------------------------


class TestIntervalMapping:
    """Tests for inspection interval mapping via threshold bands (D-03)."""

    def test_interval_mapping_emergency(self):
        """composite>=200 -> 'emergency'; also red_flag present -> 'emergency' regardless of score."""
        # Case 1: composite >= 200
        assessment = date(2026, 3, 15)
        result = compute_risk(
            structure={"type": "dam", "wear_percentage": 0},
            facts=[],
            inspections=[],
            assessment_date=assessment,
        )
        # condition=100, consequence=2.0, seasonal=1.5, staleness=1.5 -> composite=450
        assert result.composite_score >= 200
        assert result.inspection_interval == "emergency"

        # Case 2: red_flag present, low composite
        assessment2 = date(2026, 6, 26)
        result2 = compute_risk(
            structure={"type": "canal", "wear_percentage": 85},
            facts=[],
            inspections=[_inspection(30, assessment2)],
            assessment_date=assessment2,
        )
        # wear=85 triggers red_flag, composite is low
        assert len(result2.red_flags) > 0
        assert result2.inspection_interval == "emergency"

    def test_interval_mapping_30d(self):
        """composite in [150, 200) -> '30d'."""
        assessment = date(2026, 3, 15)
        result = compute_risk(
            structure={"type": "dam", "wear_percentage": 40},
            facts=[],
            inspections=[_inspection(181, assessment)],
            assessment_date=assessment,
        )
        # composite = 60 * 2.0 * 1.5 * 1.0 = 180 -> "30d"
        assert 150 <= result.composite_score < 200
        assert result.inspection_interval == "30d"

    def test_interval_mapping_90d(self):
        """composite in [100, 150) -> '90d'."""
        assessment = date(2026, 1, 15)
        result = compute_risk(
            structure={"type": "dam", "wear_percentage": 50},
            facts=[],
            inspections=[_inspection(184, assessment)],
            assessment_date=assessment,
        )
        # composite = 50 * 2.0 * 1.2 * 1.0 = 120 -> "90d"
        assert 100 <= result.composite_score < 150
        assert result.inspection_interval == "90d"

    def test_interval_mapping_180d(self):
        """composite in [60, 100) -> '180d'."""
        assessment = date(2026, 2, 15)
        result = compute_risk(
            structure={"type": "dam", "wear_percentage": 60},
            facts=[],
            inspections=[_inspection(184, assessment)],
            assessment_date=assessment,
        )
        # composite = 40 * 2.0 * 1.2 * 1.0 = 96 -> "180d"
        assert 60 <= result.composite_score < 100
        assert result.inspection_interval == "180d"

    def test_interval_mapping_12mo(self):
        """composite in [30, 60) -> '12mo'."""
        assessment = date(2026, 6, 15)
        result = compute_risk(
            structure={"type": "dam", "technical_condition": "\u043d\u0435\u0443\u0434\u043e\u0432\u043b\u0435\u0442\u0432\u043e\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435"},
            facts=[],
            inspections=[_inspection(182, assessment)],
            assessment_date=assessment,
        )
        # condition=30, consequence=2.0, seasonal=0.8, staleness=1.0 -> composite=48 -> "12mo"
        assert 30 <= result.composite_score < 60
        assert result.inspection_interval == "12mo"

    def test_interval_mapping_24mo(self):
        """composite < 30 -> '24mo'."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 75},
            facts=[],
            inspections=[_inspection(30, assessment)],
            assessment_date=assessment,
        )
        # condition=25, consequence=1.0, seasonal=0.8, staleness=0.5 -> composite=10 -> "24mo"
        assert result.composite_score < 30
        assert result.inspection_interval == "24mo"


# ---------------------------------------------------------------------------
# D-07: Red-flag detection
# ---------------------------------------------------------------------------


class TestRedFlags:
    """Tests for red-flag detection (D-07)."""

    def test_red_flag_wear_ge_80(self):
        """wear_percentage=85 -> red_flags contains 'wear_percentage_ge_80'."""
        flags = detect_red_flags(85, None, None, None)
        assert "wear_percentage_ge_80" in flags

    def test_red_flag_avarialnoe(self):
        """technical_condition='аварийное' -> red_flags contains 'emergency_condition'."""
        flags = detect_red_flags(None, "\u0430\u0432\u0430\u0440\u0438\u0439\u043d\u043e\u0435", None, None)
        assert "emergency_condition" in flags

    def test_red_flag_seepage_keyword(self):
        """findings text contains 'просачивание' -> red_flags contains 'keyword:просачивание'."""
        flags = detect_red_flags(None, None, "\u043e\u0431\u043d\u0430\u0440\u0443\u0436\u0435\u043d\u043e \u043f\u0440\u043e\u0441\u0430\u0447\u0438\u0432\u0430\u043d\u0438\u0435 \u0447\u0435\u0440\u0435\u0437 \u0434\u0430\u043c\u0431\u0443", None)
        assert "keyword:\u043f\u0440\u043e\u0441\u0430\u0447\u0438\u0432\u0430\u043d\u0438\u0435" in flags

    def test_red_flag_deformation_keyword(self):
        """findings text contains 'деформация' -> red_flags contains 'keyword:деформация'."""
        flags = detect_red_flags(None, None, "\u0437\u0430\u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u043d\u0430 \u0434\u0435\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u0433\u0440\u0435\u0431\u043d\u044f", None)
        assert "keyword:\u0434\u0435\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f" in flags

    def test_red_flag_clean(self):
        """wear=30, condition='хорошее', no keywords -> red_flags is empty list."""
        flags = detect_red_flags(30, "\u0445\u043e\u0440\u043e\u0448\u0435\u0435", None, None)
        assert flags == []


# ---------------------------------------------------------------------------
# D-08: Repair status determination
# ---------------------------------------------------------------------------


class TestRepairStatus:
    """Tests for repair status mapping via blended score (D-08)."""

    def test_repair_status_normal(self):
        """condition_score=25, no red_flags, no weak evidence -> 'normal'."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 75},
            facts=[],
            inspections=[_inspection(30, assessment)],
            assessment_date=assessment,
        )
        assert result.condition_score == pytest.approx(25.0)
        assert result.red_flags == []
        assert result.weak_evidence_reasons == []
        assert result.repair_status == "normal"

    def test_repair_status_inspection_required(self):
        """condition_score=50 -> 'inspection_required'."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 50},
            facts=[],
            inspections=[_inspection(30, assessment)],
            assessment_date=assessment,
        )
        assert result.condition_score == pytest.approx(50.0)
        assert result.repair_status == "inspection_required"

    def test_repair_status_repair_required(self):
        """condition_score=75 -> 'repair_required'."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 25},
            facts=[],
            inspections=[_inspection(30, assessment)],
            assessment_date=assessment,
        )
        assert result.condition_score == pytest.approx(75.0)
        assert result.repair_status == "repair_required"

    def test_repair_status_critical_condition(self):
        """condition_score=95 -> 'critical_condition'."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 5},
            facts=[],
            inspections=[_inspection(30, assessment)],
            assessment_date=assessment,
        )
        assert result.condition_score == pytest.approx(95.0)
        assert result.repair_status == "critical_condition"

    def test_repair_status_red_flag_override(self):
        """condition_score=25 BUT red_flag present -> 'critical_condition'."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 75},
            facts=[],
            inspections=[_inspection(30, assessment, findings="\u043e\u0431\u043d\u0430\u0440\u0443\u0436\u0435\u043d\u043e \u043f\u0440\u043e\u0441\u0430\u0447\u0438\u0432\u0430\u043d\u0438\u0435")],
            assessment_date=assessment,
        )
        assert result.condition_score == pytest.approx(25.0)
        assert len(result.red_flags) > 0
        assert result.repair_status == "critical_condition"


# ---------------------------------------------------------------------------
# D-09: Weak evidence floor
# ---------------------------------------------------------------------------


class TestWeakEvidence:
    """Tests for weak-evidence floor (D-09)."""

    def test_weak_evidence_never_inspected(self):
        """condition_score=25 (would be 'normal'), no inspections -> floored to 'inspection_required'."""
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 75},
            facts=[],
            inspections=[],
            assessment_date=date(2026, 6, 26),
        )
        assert result.condition_score == pytest.approx(25.0)
        assert "never_inspected" in result.weak_evidence_reasons
        assert result.repair_status == "inspection_required"

    def test_weak_evidence_low_confidence(self):
        """provenance_confidence='LOW', condition_score=25 -> floored to 'inspection_required'."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 75, "provenance_confidence": "LOW"},
            facts=[],
            inspections=[_inspection(30, assessment)],
            assessment_date=assessment,
        )
        assert result.condition_score == pytest.approx(25.0)
        assert "low_confidence_provenance" in result.weak_evidence_reasons
        assert result.repair_status == "inspection_required"

    def test_weak_evidence_stale_24mo(self):
        """days_since=800, condition_score=25 -> floored to 'inspection_required'."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 75},
            facts=[],
            inspections=[_inspection(800, assessment)],
            assessment_date=assessment,
        )
        assert result.condition_score == pytest.approx(25.0)
        assert "stale_inspection_24mo" in result.weak_evidence_reasons
        assert result.repair_status == "inspection_required"

    def test_weak_evidence_no_downgrade_above_floor(self):
        """condition_score=75 (already 'repair_required'), weak evidence -> stays 'repair_required'."""
        result = compute_risk(
            structure={"type": "canal", "wear_percentage": 25},
            facts=[],
            inspections=[],
            assessment_date=date(2026, 6, 26),
        )
        assert result.condition_score == pytest.approx(75.0)
        assert len(result.weak_evidence_reasons) > 0
        assert result.repair_status == "repair_required"


# ---------------------------------------------------------------------------
# Contributing factors and dataclass structure
# ---------------------------------------------------------------------------


class TestContributingFactors:
    """Tests for contributing_factors population and RiskAssessment structure."""

    def test_contributing_factors_populated(self):
        """result.contributing_factors contains wear_percentage, technical_condition, structure_type, days_since_last_inspection keys."""
        assessment = date(2026, 6, 26)
        result = compute_risk(
            structure={"type": "dam", "wear_percentage": 40, "technical_condition": "\u0445\u043e\u0440\u043e\u0448\u0435\u0435"},
            facts=[],
            inspections=[_inspection(100, assessment)],
            assessment_date=assessment,
        )
        cf = result.contributing_factors
        assert "wear_percentage" in cf
        assert "technical_condition" in cf
        assert "structure_type" in cf
        assert "days_since_last_inspection" in cf

    def test_risk_assessment_dataclass_fields(self):
        """RiskAssessment has all required fields."""
        field_names = {f.name for f in dataclass_fields(RiskAssessment)}
        expected = {
            "condition_score",
            "consequence_factor",
            "seasonal_modifier",
            "staleness_modifier",
            "composite_score",
            "inspection_interval",
            "repair_status",
            "red_flags",
            "contributing_factors",
            "weak_evidence_reasons",
        }
        assert expected.issubset(field_names)
