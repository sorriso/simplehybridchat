# path: backend/Dockerfile
# version: 5.3
#
# Development environment with hot reload
# Based on Chainguard Wolfi-based Python image
FROM cgr.dev/chainguard/python:latest-dev AS builder

# Switch to root to install system packages
USER root
WORKDIR /app

# Install build dependencies using apk (Wolfi package manager)
# Note: package names differ from Alpine
RUN apk add --no-cache build-base

# Switch back to nonroot user for pip install
USER nonroot

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM cgr.dev/chainguard/python:latest
WORKDIR /app

# Copy installed packages from nonroot user home
COPY --from=builder /home/nonroot/.local /home/nonroot/.local
COPY src/ ./src/

ENV PATH=/home/nonroot/.local/bin:$PATH

EXPOSE 8000

# Hot reload enabled for development (volume mount overrides src/)
# Use full path to uvicorn binary
CMD ["/home/nonroot/.local/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]