---
phase: 2
slug: data-ingestion-spatial-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-26
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `apps/api/pyproject.toml` ([tool.pytest.ini_options]) |
| **Quick run command** | `cd apps/api && python -m pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `cd apps/api && python -m pytest tests/ -v --timeout=60` |
| **Estimated runtime** | ~15 seconds (unit), ~60 seconds (with integration) |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/ -v --timeout=60`
- **Before `/gsd-verify-work`:** Full suite must be green + integration tests (with Docker stack) green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DATA-01 | — | N/A | unit | `pytest tests/test_ingestion.py::test_parse_kazvodhoz_sheet -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | DATA-01 | — | N/A | unit | `pytest tests/test_ingestion.py::test_provenance_creation -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | DATA-01 | — | N/A | unit | `pytest tests/test_ingestion.py::test_idempotent_ingestion -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | DATA-01 | — | N/A | unit | `pytest tests/test_ingestion.py::test_cell_type_handling -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | DATA-08 | T-02-01 | SQLAlchemy ORM parameterized queries for FTS | unit | `pytest tests/test_structures.py::test_fts_search -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | DATA-08 | — | N/A | unit | `pytest tests/test_structures.py::test_fuzzy_search -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | DATA-08 | — | N/A | unit | `pytest tests/test_structures.py::test_combined_search -x` | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 2 | DATA-08 | — | N/A | unit | `pytest tests/test_structures.py::test_filter_structures -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | INT-01 | T-02-02 | TiPG CQL2 parser prevents injection | integration | `pytest tests/test_tipg.py::test_ogc_collection_exists -x -m integration` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | INT-01 | T-02-02 | TiPG CQL2 parser prevents injection | integration | `pytest tests/test_tipg.py::test_cql2_filter -x -m integration` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 1 | INT-03 | — | Pydantic validates request bodies | unit | `pytest tests/test_structures.py::test_create_structure -x` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 1 | INT-03 | — | N/A | unit | `pytest tests/test_structures.py::test_get_structure -x` | ❌ W0 | ⬜ pending |
| 02-04-03 | 04 | 1 | INT-03 | — | N/A | unit | `pytest tests/test_structures.py::test_list_pagination -x` | ❌ W0 | ⬜ pending |
| 02-04-04 | 04 | 2 | INT-03 | T-02-03 | Parse bbox to floats, validate 4 values, ST_MakeEnvelope | integration | `pytest tests/test_structures.py::test_bbox_filter -x -m integration` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/api/tests/test_structures.py` — stubs for DATA-08, INT-03 (CRUD, search, filter, pagination)
- [ ] `apps/api/tests/test_ingestion.py` — stubs for DATA-01 (parsing, idempotency, provenance, cell types)
- [ ] `apps/api/tests/test_tipg.py` — stubs for INT-01 (OGC API collection, CQL2) — integration marker
- [ ] `apps/api/tests/conftest.py` — add structure fixtures, mock spreadsheet data
- [ ] Framework install: `xlrd` already installed; no additional framework needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| QGIS connects to TiPG OGC API Features | INT-01 | Requires QGIS desktop application | 1. Start Docker stack. 2. Open QGIS. 3. Add Vector Layer → OGC API Features. 4. URL: http://localhost:8080/collections/public.structures/items. 5. Verify structures load with filtering. |
| TiPG TileJSON renders in browser | INT-01 | Visual verification of tile rendering | 1. Start Docker stack. 2. Open http://localhost:8080/collections/public.structures/tilejson in browser. 3. Verify TileJSON response. 4. Load tiles in a map preview. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
