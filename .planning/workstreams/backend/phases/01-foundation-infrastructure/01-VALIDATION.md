---
phase: 1
slug: foundation-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]` with `asyncio_mode = "auto"`) |
| **Quick run command** | `cd apps/api && uv run pytest tests/ -x -v` |
| **Full suite command** | `cd apps/api && uv run pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && uv run pytest tests/ -x -v`
- **After every plan wave:** Run `cd apps/api && uv run pytest tests/ -v --tb=short` + `docker compose up -d && docker compose ps` (verify all healthy)
- **Before `/gsd-verify-work`:** Full suite must be green + all Docker services healthy
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DATA-07 | — | N/A | unit + integration | `cd apps/api && uv run pytest tests/test_provenance.py -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DATA-07 | — | N/A | integration | `cd apps/api && uv run pytest tests/test_provenance.py::test_fact_has_provenance -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | INT-04 | T-01-04 | Presigned URLs with short expiry | integration | `cd apps/api && uv run pytest tests/test_minio.py -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | INT-04 | — | N/A | integration | `cd apps/api && uv run pytest tests/test_schema.py::test_geometry_in_postgis -x` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | SC-1 | — | N/A | smoke (manual) | `docker compose ps` — all services "healthy" | N/A | ⬜ pending |
| 01-01-06 | 01 | 1 | SC-2 | — | N/A | integration | `cd apps/api && uv run pytest tests/test_provenance.py::test_query_by_source -x` | ❌ W0 | ⬜ pending |
| 01-01-07 | 01 | 1 | SC-3 | T-01-04 | Presigned URL roundtrip works | integration | `cd apps/api && uv run pytest tests/test_minio.py::test_presigned_roundtrip -x` | ❌ W0 | ⬜ pending |
| 01-01-08 | 01 | 1 | SC-4 | — | No binary data in PostGIS | integration | `cd apps/api && uv run pytest tests/test_schema.py::test_no_binary_in_postgis -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/api/tests/conftest.py` — shared fixtures (async DB session, test MinIO client, test client)
- [ ] `apps/api/tests/test_health.py` — health endpoint tests (DB, Redis, MinIO checks)
- [ ] `apps/api/tests/test_provenance.py` — provenance CRUD + query tests (DATA-07)
- [ ] `apps/api/tests/test_minio.py` — presigned URL roundtrip tests (INT-04, SC-3)
- [ ] `apps/api/tests/test_schema.py` — schema validation tests (INT-04, SC-4)
- [ ] Framework install: `uv add --dev pytest pytest-asyncio httpx` — if not present in initial `pyproject.toml`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| All Docker Compose services report healthy | SC-1 | Requires running Docker daemon and all containers | `docker compose up -d && docker compose ps` — verify all services show "healthy" status |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
