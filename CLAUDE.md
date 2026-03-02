# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Management

Always use `uv` to manage dependencies and run Python files — never use `pip` or `python` directly.

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package>

# Remove a dependency
uv remove <package>

# Run a Python file
uv run <file>.py
```

## Setup & Running

```bash
# Install dependencies
uv sync

# Create .env with your Anthropic API key
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY=sk-ant-...

# Start the server (from project root)
./run.sh

# Or manually
cd backend && uv run uvicorn app:app --reload --port 8000
```

App runs at `http://localhost:8000`. No separate test suite exists.

## Architecture

This is a full-stack RAG chatbot. FastAPI serves both the REST API and the frontend static files from a single process on port 8000.

**Request flow for a user query:**
1. Browser POSTs `{ query, session_id }` to `/api/query`
2. `RAGSystem` (the central orchestrator) wraps the query and fetches conversation history from `SessionManager`
3. `AIGenerator` makes a first Claude API call with the `search_course_content` tool available
4. If Claude invokes the tool, `CourseSearchTool` → `VectorStore` performs a semantic search against ChromaDB and returns formatted chunks
5. A second Claude API call synthesizes the final answer from the retrieved chunks
6. Sources and response are returned to the browser; session history is updated

**Key architectural decisions:**
- The server runs from the `backend/` directory (`cd backend && uvicorn app:app`), so all relative paths in the code (e.g. `../docs`, `./chroma_db`) are relative to `backend/`
- ChromaDB uses two collections: `course_catalog` (one doc per course, used for fuzzy course name resolution) and `course_content` (chunked lesson text, used for semantic search)
- Course name resolution is itself a vector search — when the tool is called with a `course_name`, it queries `course_catalog` first to find the closest matching title, then uses that exact title as a filter on `course_content`
- Conversation history is stored in-memory in `SessionManager` (lost on restart), capped at `MAX_HISTORY=2` exchanges (4 messages)
- The tool-use agentic loop is kept to a single round: one optional tool call, then a final answer

**Document format** (`docs/*.txt`):
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: <title>
Lesson Link: <url>
<content...>

Lesson 1: <title>
...
```
Documents are chunked into ~800-character sentence-aware segments with 100-character overlap. On startup, `app.py` loads all `.txt/.pdf/.docx` files from `../docs` into ChromaDB, skipping courses that are already indexed by title.

## Key Files

| File | Role |
|------|------|
| `backend/rag_system.py` | Central orchestrator — wires all components |
| `backend/ai_generator.py` | Claude API client; handles the tool-use agentic loop |
| `backend/vector_store.py` | ChromaDB wrapper; `SearchResults` dataclass |
| `backend/search_tools.py` | `Tool` ABC, `CourseSearchTool`, `ToolManager` |
| `backend/document_processor.py` | Parses course `.txt` files; sentence-based chunker |
| `backend/session_manager.py` | In-memory conversation history |
| `backend/config.py` | All tuneable settings (`CHUNK_SIZE`, `MAX_RESULTS`, model name, etc.) |

## Configuration (`backend/config.py`)

| Setting | Default | Purpose |
|---------|---------|---------|
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Claude model used |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model |
| `CHUNK_SIZE` | `800` | Max characters per chunk |
| `CHUNK_OVERLAP` | `100` | Overlap characters between chunks |
| `MAX_RESULTS` | `5` | Top-k chunks returned per search |
| `MAX_HISTORY` | `2` | Conversation exchanges remembered |
| `CHROMA_PATH` | `./chroma_db` | ChromaDB persistence directory (relative to `backend/`) |
