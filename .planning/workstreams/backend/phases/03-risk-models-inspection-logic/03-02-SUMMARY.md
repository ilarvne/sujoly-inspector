---
phase: 03-risk-models-inspection-logic
plan: 02
subsystem: auth
tags: [jwt, rbac, fastapi, pyjwt, sqlalchemy, postgis]

# Dependency graph
requires:
  - phase: 02-data-ingestion-foundation
    provides: Structure CRUD endpoints, async_session, Base, settings pattern
provides:
  - JWT auth endpoints (POST /auth/token, GET /auth/me)
  - require_role() dependency factory for RBAC enforcement
  - get_current_user() dependency for authenticated user extraction
  - UserModel ORM with four-role enum (admin/engineer/inspector/viewer)
  - Users table migration (0003)
  - Admin user seeding on startup
  - RBAC retrofit on structure CRUD endpoints per D-12
  - Router auto-discovery via pkgutil.iter_modules
affects: [03-03, 03-04, 03-05, 03-06]

# Tech tracking
tech-stack:
  added: [pyjwt>=2.13.0, weasyprint>=69.0, jinja2>=3.1.6]
  patterns: [JWT-HS256 auth, OAuth2PasswordBearer, require_role factory, dependency_overrides testing, router auto-discovery, admin seeding in lifespan]

key-files:
  created:
    - apps/api/src/api/routes/auth.py
    - apps/api/src/api/dependencies/auth.py
    - apps/api/src/api/dependencies/__init__.py
    - apps/api/src/api/services/auth_service.py
    - apps/api/src/api/schemas/auth.py
    - apps/api/src/api/models/user.py
    - apps/api/alembic/versions/0003_users.py
  modified:
    - apps/api/src/api/routes/structures.py
    - apps/api/src/api/models/__init__.py
    - apps/api/src/api/config/settings.py
    - apps/api/src/api/main.py
    - apps/api/pyproject.toml
    - apps/api/tests/conftest.py
    - apps/api/tests/test_auth.py
    - apps/api/tests/test_structures.py
    - .env.example
    - docker-compose.yml

key-decisions:
  - "Used app.dependency_overrides for FastAPI test auth mocking instead of unittest.mock.patch (MagicMock signature breaks FastAPI dependency resolution)"
  - "Soft-reset WIP commit from aborted executor and combined with new implementation into single proper Task 3 commit"
  - "Added async_session mock to test_client/auth_client fixtures to handle admin seeding in lifespan without real DB"

patterns-established:
  - "Auth dependency pattern: require_role('engineer') as Depends() parameter for RBAC on endpoints"
  - "Testing pattern: app.dependency_overrides[get_current_user] for role-specific test scenarios"
  - "Migration pattern: CheckConstraint for role enum validation at DB level"

requirements-completed: [RISK-07]

# Metrics
duration: 9min
completed: 2026-06-26
---

# Phase 03 Plan 02: Auth + RBAC Summary

**JWT-based authentication with four-role RBAC hierarchy (viewer/inspector/engineer/admin), require_role() dependency factory, and D-12 permissions matrix retrofit on structure CRUD endpoints**

## Performance

- **Duration:** 9 min (resumed from aborted executor)
- **Started:** 2026-06-26T01:28:45Z
- **Completed:** 2026-06-26T01:37:53Z
- **Tasks:** 3
- **Files modified:** 12 created, 10 modified

## Accomplishments
- JWT auth endpoints (POST /auth/token via username or API key, GET /auth/me) with HS256 signing
- require_role() dependency factory enforcing viewer < inspector < engineer < admin hierarchy
- RBAC retrofit on structure endpoints per D-12: create/update require engineer+, delete requires admin, GET remains open
- Users table with role CheckConstraint and admin seeding on startup
- Router auto-discovery replacing explicit include_router calls
- All Phase 3 dependencies installed (pyjwt, weasyprint, jinja2)

## Task Commits

Each task was committed atomically:

1. **Task 1: Infrastructure setup** - `2251c96` (chore: deps, settings, docker, router auto-discovery)
2. **Task 2: RED — Failing auth + RBAC tests** - `48c01b5` (test: auth tests + RBAC retrofit tests)
3. **Task 3: GREEN — Implement auth + RBAC** - `ba5c59a` (feat: JWT auth, users table, RBAC retrofit)

## Files Created/Modified

### Created
- `apps/api/src/api/routes/auth.py` - POST /auth/token and GET /auth/me endpoints
- `apps/api/src/api/dependencies/auth.py` - get_current_user, require_role factory, oauth2_scheme
- `apps/api/src/api/dependencies/__init__.py` - Barrel export for auth dependencies
- `apps/api/src/api/services/auth_service.py` - JWT encode/decode + user lookups (by username, id, api_key)
- `apps/api/src/api/schemas/auth.py` - TokenRequest, TokenResponse, UserResponse Pydantic schemas
- `apps/api/src/api/models/user.py` - UserModel ORM with four-role enum CheckConstraint
- `apps/api/alembic/versions/0003_users.py` - Users table migration with role constraint + indexes

### Modified
- `apps/api/src/api/routes/structures.py` - RBAC retrofit: require_role("engineer") on create/update, require_role("admin") on delete
- `apps/api/src/api/models/__init__.py` - Added UserModel import
- `apps/api/src/api/config/settings.py` - Added jwt_secret, jwt_expiry_hours, initial_admin_username, initial_admin_api_key
- `apps/api/src/api/main.py` - Router auto-discovery via pkgutil, admin user seeding in lifespan
- `apps/api/pyproject.toml` - Added pyjwt, weasyprint, jinja2 dependencies
- `apps/api/tests/conftest.py` - Mock user fixtures, auth_client, dependency_overrides pattern, async_session mock
- `apps/api/tests/test_auth.py` - Token/me/require_role tests with async handling
- `apps/api/tests/test_structures.py` - TestStructureRBAC class with D-12 matrix tests
- `.env.example` - JWT auth section with secret generation guidance
- `docker-compose.yml` - celery-beat service, JWT env vars on api/celery-worker/celery-beat

## Decisions Made
- **app.dependency_overrides over unittest.mock.patch for FastAPI auth tests**: MagicMock-based patching breaks FastAPI's dependency resolution (inspects mock's signature, produces 422 errors). Using `app.dependency_overrides[get_current_user]` is the idiomatic FastAPI approach and works correctly.
- **Combined WIP + new files into single Task 3 commit**: The aborted executor left a WIP commit with core implementation files. Soft-reset it and combined all Task 3 implementation into one proper `feat` commit.
- **async_session mock in test fixtures**: The admin seeding code in lifespan uses `async_session` directly, which requires a real DB connection. Added mock to test_client and auth_client fixtures to prevent startup failures.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_client fixture MagicMock signature issue with FastAPI dependency resolution**
- **Found during:** Task 3 (GREEN implementation)
- **Issue:** `patch("api.dependencies.auth.get_current_user", return_value=mock_user)` creates a MagicMock that FastAPI inspects for signature parameters, producing 422 "Field required" errors for 'args' and 'kwargs'
- **Fix:** Replaced with `app.dependency_overrides[get_current_user] = _override_get_current_user` pattern using a proper async function
- **Files modified:** apps/api/tests/conftest.py, apps/api/tests/test_structures.py
- **Verification:** All 27 auth + structure tests pass (was 0/27 before fix)

**2. [Rule 1 - Bug] Fixed require_role tests calling async function synchronously**
- **Found during:** Task 3 (GREEN implementation)
- **Issue:** Tests called `checker(mock_user)` but `require_role` returns an async function — result was coroutine object, not the expected return value
- **Fix:** Changed to `asyncio.run(checker(mock_user))` for proper async execution
- **Files modified:** apps/api/tests/test_auth.py
- **Verification:** test_require_role_* tests now pass correctly

**3. [Rule 2 - Missing Critical] Added async_session mock to test fixtures for admin seeding in lifespan**
- **Found during:** Task 3 (GREEN implementation)
- **Issue:** After Task 1 added admin seeding to lifespan, test_client fixture crashed during TestClient startup because async_session tried to connect to real PostgreSQL
- **Fix:** Added mock async_session context manager to test_client and auth_client fixtures
- **Files modified:** apps/api/tests/conftest.py
- **Verification:** TestClient starts successfully, all tests pass

**4. [Rule 1 - Bug] Fixed test_me_without_token and test_me_with_invalid_token using overridden auth**
- **Found during:** Task 3 (GREEN implementation)
- **Issue:** These tests used test_client which has get_current_user overridden to always return admin, so unauthenticated requests still got 200 OK instead of 401
- **Fix:** Created raw TestClient without dependency_overrides for these specific tests, patching only MinIO and async_session for lifespan
- **Files modified:** apps/api/tests/test_auth.py
- **Verification:** Both tests now correctly return 401

**5. [Rule 1 - Bug] Fixed test_create_structure_engineer_allowed missing provenance_id and incomplete mock**
- **Found during:** Task 3 (GREEN implementation)
- **Issue:** Test was missing provenance_id query param (required by endpoint) and mock structure lacked fields needed by StructureResponse validation
- **Fix:** Added provenance_id to request URL, used _make_mock_structure() from conftest for complete mock
- **Files modified:** apps/api/tests/test_structures.py
- **Verification:** Test passes with 201 status code

---

**Total deviations:** 5 auto-fixed (3 bugs, 1 missing critical, 1 bug in test setup)
**Impact on plan:** All auto-fixes were test infrastructure issues discovered when running the GREEN tests. The actual implementation code (auth_service, dependencies, routes, migration) worked correctly from the WIP commit. No scope creep.

## Issues Encountered
- Aborted executor left WIP commit — resolved by soft-resetting and combining into proper Task 3 commit
- FastAPI TestClient + MagicMock dependency patching incompatibility — resolved with dependency_overrides pattern

## Next Phase Readiness
- Auth foundation complete: require_role() and get_current_user available for all Phase 3 endpoints
- Plans 03-03 through 03-06 can use `Depends(require_role("engineer"))` and `Depends(get_current_user)` on new endpoints
- Admin user seeds automatically on startup from env vars
- Users migration 0003 ready for `alembic upgrade head`

## Self-Check: PASSED

All files exist, all commits found, SUMMARY.md created.

---
*Phase: 03-risk-models-inspection-logic*
*Completed: 2026-06-26*
