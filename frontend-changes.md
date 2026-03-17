# Frontend Changes

## Code Quality Tooling

### Added Prettier for automatic code formatting

**Files created:**

| File | Purpose |
|------|---------|
| `frontend/package.json` | npm project config; defines `format` and `format:check` scripts |
| `frontend/.prettierrc` | Prettier configuration (4-space indent, single quotes, 100 print width) |
| `frontend/.prettierignore` | Excludes `node_modules/` from formatting |
| `scripts/format-frontend.sh` | Dev script for running formatting checks (see usage below) |

**Files formatted by Prettier:**
- `frontend/index.html`
- `frontend/script.js`
- `frontend/style.css`

### Prettier configuration (`frontend/.prettierrc`)

```json
{
    "printWidth": 100,
    "tabWidth": 4,
    "useTabs": false,
    "semi": true,
    "singleQuote": true,
    "trailingComma": "es5",
    "bracketSpacing": true,
    "htmlWhitespaceSensitivity": "css",
    "endOfLine": "lf"
}
```

Settings chosen to match the existing code style (4-space indentation, single quotes in JS).

### Usage

**Install dependencies (first time):**
```bash
cd frontend && npm install
```

**Format all frontend files:**
```bash
# Using the dev script (from project root)
./scripts/format-frontend.sh
# or
./scripts/format-frontend.sh --fix

# Using npm scripts directly (from frontend/)
cd frontend && npm run format
```

**Check formatting without modifying files (e.g. in CI):**
```bash
# Using the dev script (from project root)
./scripts/format-frontend.sh --check

# Using npm scripts directly (from frontend/)
cd frontend && npm run format:check
```

---

# Testing Framework Changes

## Summary

Enhanced the existing testing framework for the RAG system with API endpoint testing infrastructure.

## Files Changed

### `pyproject.toml`
- Added `httpx>=0.27.0` to the `[dependency-groups] dev` section (required by FastAPI's `TestClient`)
- Added `[tool.pytest.ini_options]` with:
  - `testpaths = ["backend/tests"]` — pytest auto-discovers tests without needing to specify the path
  - `pythonpath = ["backend"]` — adds the `backend/` directory to `sys.path` so test modules can import backend code without the manual `sys.path.insert` hack in each file

### `backend/tests/conftest.py`
Added three new shared fixtures for API testing:

- **`mock_rag_system`** — a `MagicMock` of `RAGSystem` with sensible defaults (`query` returns a response + source list, `get_course_analytics` returns two sample courses, `create_session` returns a fixed session ID)
- **`test_app`** — a minimal `FastAPI` application that mirrors the real `app.py` API routes (`POST /api/query`, `GET /api/courses`) but **does not mount the frontend static files**, avoiding `FileNotFoundError` when `../frontend` doesn't exist in the test environment. Receives `mock_rag_system` as a parameter so each test can control RAG behaviour.
- **`api_client`** — a `fastapi.testclient.TestClient` wrapping `test_app`, ready for synchronous HTTP calls in tests.

### `backend/tests/test_api_endpoints.py` *(new file)*
18 tests covering the two API endpoints:

**`POST /api/query`**
- Returns HTTP 200 for a valid payload
- Response contains `answer`, `sources`, and `session_id` fields with correct types
- Passes an explicit `session_id` through to `rag_system.query` unchanged
- Auto-creates a session via `session_manager.create_session()` when no `session_id` is provided
- Returns HTTP 422 when the required `query` field is missing
- Delegates query processing to `rag_system.query`
- Returns HTTP 500 and exposes the error message when `rag_system.query` raises

**`GET /api/courses`**
- Returns HTTP 200
- Response contains `total_courses` (int) and `course_titles` (list) fields
- `total_courses` matches `len(course_titles)`
- Delegates to `rag_system.get_course_analytics`
- Returns HTTP 500 and exposes the error message when `get_course_analytics` raises
