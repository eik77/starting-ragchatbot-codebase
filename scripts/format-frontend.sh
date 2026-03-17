#!/usr/bin/env bash
# Format and check frontend code quality

set -e

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../frontend" && pwd)"

echo "Running frontend quality checks..."
echo "Frontend dir: $FRONTEND_DIR"

cd "$FRONTEND_DIR"

# Install deps if node_modules is missing
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

case "${1:-}" in
    --check)
        echo "Checking formatting (no files will be changed)..."
        ./node_modules/.bin/prettier --check .
        echo "All frontend files are properly formatted."
        ;;
    --fix | "")
        echo "Formatting frontend files..."
        ./node_modules/.bin/prettier --write .
        echo "Frontend formatting complete."
        ;;
    *)
        echo "Usage: $0 [--check | --fix]"
        echo "  --fix    Format files (default)"
        echo "  --check  Check formatting without modifying files"
        exit 1
        ;;
esac
