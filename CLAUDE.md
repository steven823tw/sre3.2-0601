# CLAUDE.md — SRE Platform V3.2

## Project Overview

Engineer Assist SRE Platform — FastAPI backend + React/TypeScript frontend for infrastructure management, VM migration, and AI-assisted operations.

## Architecture

```
backend/app/
├── api/v1/          # Route handlers (thin — delegate to services)
├── services/        # Business logic
├── repositories/    # Database queries
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response models
├── platforms/       # Platform adapters (vSphere, KVM, FusionSphere)
├── core/            # Database, security, registry, crypto
├── middleware/      # Audit, error handler, request ID
└── migration/       # VM migration engine

frontend/src/
├── api/             # HTTP client + API modules
├── components/      # React components (PascalCase, named exports)
├── hooks/           # Custom hooks (useXxx)
├── stores/          # Zustand stores
├── types/           # TypeScript interfaces
├── lib/             # Utilities (cn, formatBytes, formatTime, queries)
└── utils/           # Re-exports from lib/ (backwards compat)
```

## Critical Rules — NEVER VIOLATE

### 1. Frontend-Backend Contract

- **Backend Pydantic schema is the single source of truth.** Frontend TypeScript types MUST match field names exactly.
- **`httpClient` paths are relative to `/api/v1`.** NEVER include `/v1/` in paths.
- **Response shapes must match actual backend returns**, not an assumed `{success, data}` wrapper.
- **HTTP methods must match backend router decorators** (`@router.put` → `httpClient.put`).
- **Enum values must be consistent** across all layers: `vsphere`/`kvm`/`fusionsphere` (not `vmware`/`fusioncompute`).

### 2. Service Layer Rules

- **Services MUST use `AppException` subclasses** (NotFoundException, ValidationException, etc.), NEVER `HTTPException`.
- **Services MUST use `self._repo`** for CRUD operations, NEVER raw `self._session` for standard queries.
- **Services MUST NOT have side effects in test methods.** Connection testing should be stateless.

### 3. Error Handling

- **ZERO tolerance for `except:pass`.** Every catch must at minimum log `logger.warning()`.
- **Use `super().__init__()`** in exception hierarchies, NEVER `AppException.__init__()` directly.
- **AdapterError subclasses** must pass `message` as first positional arg to `super().__init__()`.

### 4. Import Rules

- **All stdlib imports at module level.** NEVER `import json` or `import re` inside functions.
- **No duplicate imports.** If `re` and `ipaddress` are imported at module level, don't re-import locally.
- **Use `@/` alias** for all cross-directory imports in frontend. NEVER use `../../` relative paths.

### 5. Validation Rules

- **Use `re.fullmatch()` not `re.match()`** for input validation (match doesn't check end of string).
- **Use `*` quantifier** for optional regex parts, not `+` (which rejects empty strings).
- **Use `shlex.quote()` or argument lists** for subprocess calls. NEVER use f-string shell commands.

### 6. Testing Rules

- **All new services MUST have tests.** Target: 80%+ coverage for services.
- **Use FastAPI `Depends()` for DI.** No module-level service singletons.
- **Tests MUST NOT use `assert x in (True, False)`** — this accepts any value. Use `assert x is True` or `assert isinstance(x, bool)`.

### 7. Naming Conventions

- **Backend**: snake_case for all Python identifiers.
- **Frontend components**: PascalCase, named exports (`export function ComponentName`).
- **Frontend types**: PascalCase interfaces, camelCase properties (except API-mirroring snake_case).
- **Platform names**: `vsphere`/`kvm`/`fusionsphere` (lowercase, no spaces).

## Commands

```bash
# Backend tests
cd backend && PYTHONIOENCODING=utf-8 APP_ENV=development JWT_SECRET_KEY=test-secret-key-for-testing-only DEV_DEFAULT_USER=test-user python -m pytest tests/ -v

# Backend syntax check
python -c "import py_compile; py_compile.compile('file.py', doraise=True)"

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend dev server
cd frontend && npm run dev
```

## Known Issues (as of 2026-06-01)

See `docs/ARCHITECTURE_CRITIQUE.html` for full gap analysis. Key remaining items:
- dashboard.py uses local DI (not centralized in dependencies.py)
- migration.py engine is bare singleton (not DI-injected)
- 65 backend functions missing return type annotations
- 4 services + 2 API routers lack tests
