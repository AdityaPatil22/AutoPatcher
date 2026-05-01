# Stage 1 — build the React frontend
FROM docker.io/library/node:22-alpine AS frontend-builder

WORKDIR /build
COPY Frontend/package.json Frontend/package-lock.json ./
RUN npm ci
COPY Frontend/ .
RUN npm run build

# Stage 2 — Python runtime serving everything
FROM docker.io/library/python:3.13-slim AS runtime

WORKDIR /app

COPY Backend/requirements.txt /app/Backend/requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install --no-cache-dir -r /app/Backend/requirements.txt && \
    apt-get purge -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY Backend/ /app/Backend/
COPY --from=frontend-builder /build/dist /app/Frontend/dist

RUN mkdir -p /app/.chroma_index
VOLUME /app/.chroma_index

EXPOSE 8000

WORKDIR /app/Backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
