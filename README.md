# AutoPatch AI

AI-powered bug fix generator. Paste a bug ticket, get a code patch back.

## How It Works

```
Bug Ticket → Context Search → LLM Prompt → Patch (diff)
```

1. **Input** a bug report (title + description) via the React frontend
2. **Context fetch** searches the indexed repository using keyword, semantic, or hybrid search
3. **Prompt builder** constructs a structured prompt with the bug + relevant code
4. **LLM** (local via Ollama, OpenAI, or Gemini) analyzes the bug and returns fixed code
5. **Diff generator** produces a unified diff showing exactly what changed

## Quick Start

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install backend dependencies
pip install -r Backend/requirements.txt

# 3. Configure environment
cp Backend/.env.example Backend/.env
# Edit Backend/.env and add your API keys (optional for local LLM)

# 4. Start the backend
cd Backend
uvicorn main:app --reload

# 5. Start the frontend (in a separate terminal)
cd Frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and proxies API calls to the backend at `http://localhost:8000`.

## API Usage

### `POST /api/generate-fix`

```bash
curl -X POST http://localhost:8000/api/generate-fix \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix export button issue",
    "description": "Export fails when user status is pending. The export_user_data function only handles active users and returns None for all other statuses.",
    "file_hint": "user_service.py"
  }'
```

**Request body:**

| Field         | Type   | Required | Description                          |
|---------------|--------|----------|--------------------------------------|
| `title`       | string | yes      | Bug ticket title                     |
| `description` | string | yes      | Detailed bug description             |
| `file_hint`   | string | no       | Filename to narrow context search    |

**Response:**

```json
{
  "ticket_title": "Fix export button issue",
  "patches": [
    {
      "file_path": "user_service.py",
      "original_code": "...",
      "fixed_code": "...",
      "diff": "--- a/user_service.py\n+++ b/user_service.py\n...",
      "warning": ""
    }
  ],
  "explanation": "The export_user_data function only handled active users..."
}
```

### `POST /api/refine-fix`

Refine a previous fix with feedback. Accepts the same fields as `generate-fix` plus `feedback` and `previous_patches`.

### `POST /api/index`

Index a repository for semantic code search.

```bash
curl -X POST http://localhost:8000/api/index \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/your/project"}'
```

### `GET /health`

Returns `{"status": "ok"}` — use for health checks.

## Project Structure

```
AutoPatch-AI/
├── Backend/
│   ├── main.py                  # FastAPI entry point
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   └── app/
│       ├── config.py            # Environment config
│       ├── models.py            # Pydantic request/response models
│       ├── routes/
│       │   ├── fix.py           # /generate-fix, /refine-fix endpoints
│       │   ├── index.py         # /index endpoints
│       │   └── settings.py      # /settings endpoints
│       ├── services/
│       │   ├── context.py       # Code search (keyword/semantic/hybrid)
│       │   ├── indexer.py       # ChromaDB semantic indexing
│       │   ├── prompt.py        # LLM prompt builder
│       │   └── llm.py           # LLM provider calls (local/OpenAI/Gemini)
│       └── utils/
│           ├── diff.py          # Unified diff generator
│           └── patch.py         # Fuzzy code patch application
├── Frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx              # Main application component
│       ├── App.css              # Styles
│       ├── api.ts               # API client
│       ├── types.ts             # TypeScript type definitions
│       └── components/
│           ├── PatchCard.tsx     # Patch display with diff viewer
│           ├── FileTree.tsx      # Indexed file explorer
│           └── IndexModal.tsx    # Repository indexing modal
└── README.md
```

## Configuration

Copy `Backend/.env.example` to `Backend/.env` and set your values:

| Variable             | Default                      | Description                               |
|----------------------|------------------------------|-------------------------------------------|
| `LLM_PROVIDER`       | `local`                      | `local`, `openai`, or `gemini`            |
| `OPENAI_API_KEY`     | —                            | Your OpenAI API key                       |
| `GEMINI_API_KEY`     | —                            | Your Google Gemini API key                |
| `LLM_MODEL`          | —                            | Model name (e.g. `llama3:8b`, `gpt-4o-mini`) |
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434/v1`  | Base URL for local LLM server (Ollama)    |
| `SAMPLE_REPO_PATH`   | —                            | Path to a repository to auto-index        |
| `SEARCH_MODE`        | `hybrid`                     | `keyword`, `semantic`, or `hybrid`        |
| `MAX_CONTEXT_FILES`  | `3`                          | Number of files to include as context     |
| `CHROMA_PERSIST_DIR` | `./.chroma_index`            | ChromaDB vector store location            |

## Example Bug Tickets to Try

**1. Export fails for non-active users**
```json
{
  "title": "Export fails for pending users",
  "description": "export_user_data returns None when user status is pending instead of raising an error or handling the case"
}
```
