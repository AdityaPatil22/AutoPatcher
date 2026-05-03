# AutoPatch AI

AI-powered bug fix generator. Paste a bug ticket, get a code patch — and optionally push it as a GitHub Pull Request.

## System Design

![AutoPatch AI System Architecture](./system-design.png)

## How It Works

```
Bug Ticket → GitHub OAuth → Index Repo → Context Search → LLM Prompt → Patch (diff) → GitHub PR
```

1. **Authenticate** via GitHub OAuth 2.0 (scopes: `read:user`, `user:email`, `repo`)
2. **Index** a GitHub repository — clones it, chunks the code, and stores embeddings in ChromaDB
3. **Input** a bug report (title + description) via the React frontend
4. **Context fetch** runs hybrid search (keyword + semantic) over indexed code
5. **Prompt builder** constructs a structured prompt with the bug + relevant code context
6. **LLM** (Google Gemini or local Ollama) analyzes the bug and returns fixed code
7. **Diff generator** produces a unified diff showing exactly what changed
8. **Create PR** — one click to push the fix as a GitHub Pull Request via the GitHub API

## Tech Stack

| Layer | Technology | Deployment |
|-------|-----------|------------|
| **Frontend** | React 19, TypeScript, Vite 8 | Railway (single container) |
| **Backend** | FastAPI, Python 3.13, Uvicorn | Railway (single container) |
| **Database** | PostgreSQL (SQLAlchemy ORM) | Neon Console (serverless) |
| **Vector DB** | ChromaDB (semantic search) | Chroma Cloud |
| **Auth** | GitHub OAuth 2.0, JWT, Fernet | — |
| **LLM** | Google Gemini API / Ollama | Cloud / Local |
| **VCS** | GitHub REST API v3 | — |
| **Container** | Multi-stage Docker build | Railway |

## Architecture Overview

### Frontend (React 19 + Vite)
- Single-page application with dark/light theme
- Diff viewer for patch visualization
- GitHub OAuth login flow
- Repository indexing modal
- One-click PR creation from generated patches

### Backend (FastAPI + Python 3.13)
- **Auth Service** — GitHub OAuth callback, JWT session cookies, Fernet-encrypted token storage
- **Context Service** — Hybrid search with fallback chain (semantic → keyword)
- **Indexer Service** — Clones GitHub repos, chunks code into overlapping segments, stores in ChromaDB
- **LLM Service** — Multi-provider support (Gemini with thinking + search, Ollama via OpenAI-compatible API)
- **Prompt Builder** — Structured prompt construction with bug context and relevant code
- **GitHub PR Service** — Branch creation, atomic commits via Git Trees API, pull request creation
- **Diff Generator** — Unified diff output with fuzzy patch application
- **Middleware** — Rate limiting, CORS, security headers (XSS, clickjacking), API key scrubbing

### Databases
- **PostgreSQL (Neon Console)** — Users, encrypted GitHub tokens, repo metadata, sessions
- **ChromaDB (Chroma Cloud)** — Per-user vector collections for code embeddings and semantic search

### External APIs
- **GitHub OAuth 2.0** — Authentication and authorization
- **GitHub REST API v3** — Repository operations, branch/tree/commit/PR management
- **Google Gemini API** — LLM inference (gemini-2.5-flash, gemini-3-flash-preview)
- **Ollama** (optional) — Local LLM via OpenAI-compatible API

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 22+
- A GitHub OAuth App ([create one](https://github.com/settings/developers))
- A Gemini API key ([get one](https://aistudio.google.com/apikey))

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/your-username/AutoPatch-AI.git
cd AutoPatch-AI

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install backend dependencies
pip install -r Backend/requirements.txt

# 4. Configure environment
cp Backend/.env.example Backend/.env
# Edit Backend/.env with your API keys and database URL

# 5. Start the backend
cd Backend
uvicorn main:app --reload

# 6. Start the frontend (separate terminal)
cd Frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and proxies API calls to the backend at `http://localhost:8000`.

### Container Deployment (Docker / Podman)

```bash
# Build the multi-stage image
docker build -t autopatch-ai .

# Run with cloud LLM
docker run -d --name autopatch -p 8000:8000 \
  --env-file Backend/.env \
  autopatch-ai

# Run with a local LLM (Ollama on host)
docker run -d --name autopatch -p 8000:8000 \
  -e LLM_PROVIDER=local \
  -e LOCAL_LLM_BASE_URL=http://host.docker.internal:11434/v1 \
  autopatch-ai
```

The app is available at `http://localhost:8000` (backend serves the built frontend).

### Railway Deployment

The project is configured for Railway with a single-container deployment:

1. Connect your GitHub repository to Railway
2. Set environment variables in the Railway dashboard (see Configuration below)
3. Railway auto-builds using the `Dockerfile` (multi-stage: Node build → Python runtime)
4. The backend serves the built frontend static files from `/Frontend/dist`

## Configuration

Copy `Backend/.env.example` to `Backend/.env` and configure:

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `local` | `local` (Ollama) or `gemini` |
| `LLM_MODEL` | — | Model name (e.g. `gemini-2.5-flash`, `llama3:8b`) |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434/v1` | Ollama / LM Studio API URL |

### GitHub OAuth

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_CLIENT_ID` | — | OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | — | OAuth App client secret |
| `SECRET_KEY` | — | Fernet key for encrypting tokens (generate below) |
| `FRONTEND_URL` | `http://localhost:5173` | Redirect URL after OAuth callback |

Generate a Fernet key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://localhost/autopatch` | PostgreSQL connection string (Neon Console) |

### ChromaDB

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_MODE` | `local` | `local`, `cloud` (Chroma Cloud), or `server` (self-hosted) |
| `CHROMA_API_KEY` | — | API key for Chroma Cloud |
| `CHROMA_TENANT` | — | Chroma Cloud tenant ID |
| `CHROMA_DATABASE` | — | Chroma Cloud database name |
| `CHROMA_HOST` | `localhost` | Self-hosted ChromaDB host |
| `CHROMA_PORT` | `8000` | Self-hosted ChromaDB port |
| `CHROMA_PERSIST_DIR` | `./.chroma_index` | Local ChromaDB storage path |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS origins |
| `RATE_LIMIT_GLOBAL` | `60` | Global requests/min per IP |
| `RATE_LIMIT_LLM` | `10` | LLM endpoint requests/min per IP |

### Other

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONTEXT_FILES` | `3` | Number of context files sent to LLM |
| `CLONE_DIR` | System temp dir | Temp directory for cloned repos |

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/auth/github` | Redirect to GitHub OAuth |
| `GET` | `/api/auth/callback` | OAuth callback (exchanges code for token) |
| `GET` | `/api/auth/me` | Get current user profile |
| `POST` | `/api/auth/logout` | Clear session cookie |

### Bug Fix Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/generate-fix` | Generate a patch from a bug ticket |
| `POST` | `/api/refine-fix` | Refine a patch with feedback |

### Repository Indexing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/index` | Index a repository for code search |
| `GET` | `/api/index/status` | Check indexing status |
| `GET` | `/api/index/files` | List indexed files |

### Pull Requests

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/create-pr` | Create a GitHub PR from patches |

### Other

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/settings` | Get current settings |
| `PUT` | `/api/settings` | Update LLM settings |

### Example: Generate a Fix

```bash
curl -X POST http://localhost:8000/api/generate-fix \
  -H "Content-Type: application/json" \
  -b "autopatch_session=<your-jwt>" \
  -d '{
    "title": "Export fails for pending users",
    "description": "export_user_data returns None when user status is pending instead of raising an error",
    "file_hint": "user_service.py"
  }'
```

**Response:**

```json
{
  "ticket_title": "Export fails for pending users",
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

## Project Structure

```
AutoPatch-AI/
├── Backend/
│   ├── main.py                  # FastAPI entry, lifespan, static file serving
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   └── app/
│       ├── config.py            # Environment config loader
│       ├── models.py            # Pydantic request/response schemas
│       ├── models_db.py         # SQLAlchemy ORM models (User)
│       ├── db.py                # Database engine, session factory
│       ├── middleware.py         # Rate limiter, security headers, key scrubber
│       ├── constants.py         # Supported extensions, skip dirs
│       ├── routes/
│       │   ├── auth.py          # GitHub OAuth + session management
│       │   ├── fix.py           # /generate-fix, /refine-fix
│       │   ├── index.py         # /index, /index/status, /index/files
│       │   ├── pr.py            # /create-pr (GitHub PR creation)
│       │   └── settings.py      # /settings (LLM provider config)
│       ├── services/
│       │   ├── context.py       # Hybrid search orchestrator with fallbacks
│       │   ├── indexer.py       # ChromaDB indexing + semantic search
│       │   ├── search_keyword.py # Keyword-based code search
│       │   ├── search_semantic.py # Semantic search via ChromaDB
│       │   ├── prompt.py        # LLM prompt construction
│       │   ├── llm.py           # LLM provider calls (Gemini / Ollama)
│       │   └── github.py        # GitHub API (branches, commits, PRs)
│       └── utils/
│           ├── diff.py          # Unified diff generator
│           └── patch.py         # Fuzzy code patch application
├── Frontend/
│   ├── package.json             # React 19, Vite 8, TypeScript 6
│   ├── vite.config.ts           # Dev server proxy config
│   └── src/
│       ├── App.tsx              # Root component
│       ├── App.css              # Global styles
│       ├── api.ts               # API client
│       ├── types.ts             # TypeScript type definitions
│       ├── hooks/               # Custom React hooks
│       │   ├── useAuth.ts       # GitHub OAuth state
│       │   ├── useIndex.ts      # Index status management
│       │   ├── useSettings.ts   # LLM settings state
│       │   ├── usePatchGeneration.ts # Patch generation flow
│       │   └── useTheme.ts      # Dark/light theme toggle
│       └── components/
│           ├── TopBar/          # Navigation, auth status, theme toggle
│           ├── InputPanel/      # Bug ticket form
│           ├── OutputPanel/     # Patch results, diff viewer, PR button
│           ├── PatchCard/       # Individual patch with diff display
│           ├── ErrorCard/       # Error display component
│           ├── FileTree/        # Indexed file explorer
│           └── IndexModal/      # Repository indexing dialog
├── Dockerfile                   # Multi-stage build (Node + Python)
├── system-design.png            # System architecture diagram
└── README.md
```

## Security

- **Fernet encryption** for GitHub access tokens at rest in PostgreSQL
- **JWT session cookies** (`httpOnly`, `sameSite=lax`, 7-day expiry)
- **Rate limiting** per IP (60 req/min global, 10 req/min LLM endpoints)
- **API key scrubbing** in error responses (defense-in-depth middleware)
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy`
- **Per-user data isolation** — separate ChromaDB collections and DB records per user

## License

MIT
