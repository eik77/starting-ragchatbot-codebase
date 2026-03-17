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
