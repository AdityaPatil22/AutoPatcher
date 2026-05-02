# Stage 1 — build the React frontend
FROM docker.io/library/node:22-alpine AS frontend-builder

WORKDIR /build
COPY Frontend/package.json Frontend/package-lock.json ./
RUN npm ci
COPY Frontend/ .
RUN npm run build

# Stage 2 — Python runtime serving everything
FROM docker.io/library/python:3.13-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY Backend/requirements.txt /app/Backend/requirements.txt
RUN pip install --no-cache-dir -r /app/Backend/requirements.txt

COPY Backend/ /app/Backend/
COPY --from=frontend-builder /build/dist /app/Frontend/dist

RUN mkdir -p /app/.chroma_index /tmp/autopatch_clones

EXPOSE 8000

ENV CHROMA_PERSIST_DIR=/app/.chroma_index
ENV CLONE_DIR=/tmp/autopatch_clones

WORKDIR /app/Backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
