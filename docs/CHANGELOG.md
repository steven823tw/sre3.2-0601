# V3.2.0 Changelog

> **Release Date**: 2026-06-01
> **Previous Version**: 3.1.0

---

## Security (Critical)

- **JWT Token Type Validation**: `decode_token()` now validates the `type` claim. Refresh tokens are rejected on API endpoints (`expected_type="access"`).
- **Full Endpoint Authentication**: All GET endpoints in `alerts`, `assets`, and `operations` routers now require `CurrentUser` authentication. Previously 7 GET endpoints were unauthenticated.
- **Rate Limiting Middleware**: New `RateLimitMiddleware` enforces per-client request limits (default: 60/min). Configured via `RATE_LIMIT_PER_MINUTE` env var. Health probes are exempt.
- **Error Message Deduplication**: Token validation errors no longer produce doubled "Token validation failed: Token validation failed:" messages.
- **Encryption Warning**: `encrypt("")` now logs a warning instead of silently returning empty string.
- **Plaintext Fallback Logging**: `_safe_decrypt()` plaintext fallback upgraded from `logger.warning` to `logger.error` with deprecation notice.

## Bug Fixes

- **Subprocess Timeout Kill**: Operation executor now properly kills child processes on timeout (`proc.kill()` + `await proc.wait()`). Added `finally` block to guarantee cleanup even on unexpected exceptions.
- **Proc Scope Guard**: `proc = None` initialization prevents `NameError` if `create_subprocess_exec` itself fails before assignment.
- **ErrorBoundary Placement**: Moved `ErrorBoundary` inside `QueryClientProvider` so a single component error doesn't destroy the entire React Query cache.
- **Chat Error Feedback**: `useChat` hook now displays error messages in the chat UI instead of silently swallowing failures.

## Performance

- **Dashboard Parallel Queries**: `DashboardService.get_summary()` now uses `asyncio.gather()` to execute 7 independent repository calls in parallel instead of sequentially.

## Architecture

- **Platform Enum Unification**: `Platform` enum values standardized to lowercase (`vsphere`, `kvm`, `fusionsphere`, `openstack`, `kubernetes`, `physical`, `other`). Schema.sql aligned.
- **Version Unification**: All version references updated to 3.2.0 (`pyproject.toml`, `config.py`, `docs/`).
- **Dead Code Removal**: Deleted unused `providers.tsx`, removed unused imports (`Any`, `Depends`) from `migration.py`.

## Testing

- **254 tests passing** (up from 246), 7 skipped (KVM adapter requires libvirt system library).
- **+8 new tests**: JWT token type validation (4), rate limiting middleware (4).

## Infrastructure

- **`.dockerignore`**: Created for both `backend/` and project root. Excludes tests, docs, `__pycache__`, `.git`, `node_modules` from Docker build context.

## Documentation

- **`docs/TEST_REPORT.md`**: Comprehensive test coverage report with 254 tests, security test matrix, environment configuration.
- **`docs/CHANGELOG.md`**: This file.
- **`docs/DEPLOYMENT_GUIDE.md`**: Version references updated to 3.2.0.
- **`docs/OPERATIONS_GUIDE.md`**: Already at V3.2, no changes needed.
- **Deleted**: `docs/FINAL_REPORT.md` (entirely V3.1), `docs/DEPLOYMENT.md` (duplicate of DEPLOYMENT_GUIDE.md).

---

## Migration Notes

### From V3.1 to V3.2

1. **Database**: No schema migration required. SQLAlchemy models use `native_enum=False` (string storage), so enum value changes (`OpenStack` → `openstack`) only affect new records.

2. **Environment Variables**: New optional variable `RATE_LIMIT_PER_MINUTE` (default: 60). Set to `0` to disable.

3. **API Changes**: All GET endpoints now require authentication. If you have scripts calling these endpoints without `Authorization: Bearer <token>`, they will receive 401 responses.

4. **Frontend**: `ErrorBoundary` moved inside `QueryClientProvider`. No API changes. `providers.tsx` deleted (was unused).
