---
phase: 03
slug: risk-models-inspection-logic
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-26
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio (already in dev dependencies) |
| **Config file** | `apps/api/pyproject.toml` `[tool.pytest.ini_options]` — asyncio_mode = "auto" |
| **Quick run command** | `cd apps/api && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | RISK-01 | T-03-01 | Risk computation uses parameterized inputs, no injection | unit | `pytest tests/test_risk_engine.py::test_compute_risk -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | RISK-02 | — | Interval mapping produces valid enum values | unit | `pytest tests/test_risk_engine.py::test_interval_mapping -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | RISK-03 | T-03-02 | Red-flag detection covers all 6 trigger conditions | unit | `pytest tests/test_risk_engine.py::test_red_flags -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 1 | RISK-04 | — | Four repair statuses via threshold bands | unit | `pytest tests/test_risk_engine.py::test_repair_status -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 1 | RISK-05 | — | Weak-evidence floor never below "inspection required" | unit | `pytest tests/test_risk_engine.py::test_weak_evidence -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | RISK-07 | T-03-03 | JWT rejects alg=none, role enforcement on all endpoints | integration | `pytest tests/test_auth.py -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | RISK-06 | T-03-04 | Override creates provenance record, requires engineer/admin role | integration | `pytest tests/test_risk_api.py::test_override -x` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 2 | DATA-05 | T-03-05 | Inspection CRUD, photos via presigned URLs (time-limited) | integration | `pytest tests/test_inspections.py -x` | ❌ W0 | ⬜ pending |
| 03-05-01 | 05 | 2 | DATA-06 | T-03-05 | Document CRUD, MinIO presigned URLs (time-limited) | integration | `pytest tests/test_documents.py -x` | ❌ W0 | ⬜ pending |
| 03-06-01 | 06 | 3 | RISK-08 | T-03-06 | CSV injection mitigation, trilingual export labels | integration | `pytest tests/test_exports.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_risk_engine.py` — stubs for RISK-01, RISK-02, RISK-03, RISK-04, RISK-05 (pure unit tests, no DB needed)
- [ ] `tests/test_auth.py` — stubs for RISK-07 (JWT encode/decode, role enforcement)
- [ ] `tests/test_risk_api.py` — stubs for RISK-06 (override endpoint with provenance)
- [ ] `tests/test_inspections.py` — stubs for DATA-05 (inspection CRUD + photo presigned URLs)
- [ ] `tests/test_documents.py` — stubs for DATA-06 (document CRUD + MinIO presigned URLs)
- [ ] `tests/test_exports.py` — stubs for RISK-08 (CSV/GeoJSON/PDF export, trilingual labels)
- [ ] Update `tests/conftest.py` — add fixtures for mock risk assessments, mock inspections, mock users, mock documents
- [ ] Framework install: WeasyPrint + PyJWT + Jinja2 (in pyproject.toml, installed via `uv sync`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PDF inspection report visual layout (Kazakh Cyrillic rendering) | RISK-08 | Font rendering and visual layout require human inspection | Generate PDF with `lang=kk`, verify ә, ғ, қ, ң, ө, ұ, һ characters render correctly |
| WeasyPrint system dependencies in Docker | RISK-08 | Container build must include Pango libraries | Build Docker image, run `python -c "import weasyprint"` inside container |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
