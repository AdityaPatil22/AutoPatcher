# AutoPatch AI

AI-powered bug fix generator. Paste a bug ticket, get a code patch back.

## How It Works

```
Bug Ticket → Context Search → LLM Prompt → Patch (diff)
```

1. **Input** a bug report (title + description)
2. **Context fetch** searches `sample_repo/` for the most relevant source file using keyword matching
3. **Prompt builder** constructs a structured prompt with the bug + code
4. **LLM** (OpenAI or Gemini) analyzes the bug and returns fixed code
5. **Diff generator** produces a unified diff showing exactly what changed

## Quick Start

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# Edit .env and add your OpenAI or Gemini API key

# 4. Start the backend
uvicorn main:app --reload

# 5. (Optional) Start the Streamlit frontend
streamlit run frontend.py
```

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
  "file_path": "user_service.py",
  "original_code": "...",
  "fixed_code": "...",
  "diff": "--- a/user_service.py\n+++ b/user_service.py\n...",
  "explanation": "The export_user_data function only handled active users..."
}
```

### `GET /health`

Returns `{"status": "ok"}` — use for health checks.

## Project Structure

```
Backend/
├── main.py                  # FastAPI entry point
├── frontend.py              # Streamlit UI
├── app/
│   ├── config.py            # Environment config
│   ├── models.py            # Pydantic request/response models
│   ├── routes/
│   │   └── fix.py           # /generate-fix endpoint
│   ├── services/
│   │   ├── context.py       # Keyword-based code search
│   │   ├── prompt.py        # LLM prompt builder
│   │   └── llm.py           # OpenAI / Gemini caller
│   └── utils/
│       └── diff.py          # Unified diff generator
├── requirements.txt
└── .env.example
```

## Configuration

Copy `.env.example` to `.env` and set your values:

| Variable           | Default                        | Description                               |
|--------------------|--------------------------------|-------------------------------------------|
| `LLM_PROVIDER`     | `openai`                       | `openai`, `gemini`, or `local`            |
| `OPENAI_API_KEY`   | —                              | Your OpenAI API key                       |
| `GEMINI_API_KEY`   | —                              | Your Google Gemini API key                |
| `LLM_MODEL`        | `gpt-4o-mini`                  | Model name to use                         |
| `LOCAL_LLM_BASE_URL`| `http://localhost:11434/v1`   | Base URL for the local model server       |
| `SAMPLE_REPO_PATH` | `./sample_repo`                | Path to the target codebase               |

## Example Bug Tickets to Try

**1. Export fails for non-active users**
```json
{
  "title": "Export fails for pending users",
  "description": "export_user_data returns None when user status is pending instead of raising an error or handling the case"
}
```

