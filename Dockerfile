# ─── CAM-CHILE Dockerfile ──────────────────────────────────────────────
# Multi-stage build para minimizar tamaño de la imagen runtime.
# Usuario no-root, healthcheck, y exposición local.
#
# ADR-0003: este Dockerfile NO incluye push a ningún registry.
#           El push a GHCR/Docker Hub requiere aprobación CEO.
# ───────────────────────────────────────────────────────────────────────

# ─────────────── Stage 1: builder ───────────────
FROM python:3.12-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Dependencias mínimas para compilar wheels con C extensions (si las hubiera).
RUN apk add --no-cache gcc musl-dev

# requirements-runtime.txt: solo lo necesario para servir el backend.
COPY requirements-runtime.txt ./
RUN pip install --user --no-cache-dir -r requirements-runtime.txt

# ─────────────── Stage 2: runtime ───────────────
FROM python:3.12-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

# wget viene de BusyBox en Alpine — no requiere install explícito.
# (Comentario conservado por trazabilidad; si se quita falla el HEALTHCHECK en algunos runners.)

# Crear usuario no-root con UID/GID numéricos (compatibilidad con Kubernetes/OCI).
RUN addgroup -S -g 1001 appuser && \
    adduser -S -u 1001 -G appuser -H -s /sbin/nologin appuser

# Copiar dependencias del builder.
COPY --from=builder /root/.local /home/appuser/.local

WORKDIR /app

# Copiar código fuente con ownership correcto.
# Solo `backend/` se incluye en runtime — `catalog/` y `scripts/` son dev/curación
# y se ejecutan fuera del contenedor (worktree del agente).
COPY --chown=appuser:appuser backend/ ./backend/

# Crear directorio para la DB SQLite con permisos correctos.
RUN mkdir -p /app/backend/db && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck via wget contra /healthz (no requiere curl).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8000/healthz || exit 1

# Comando por defecto: arrancar uvicorn.
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]