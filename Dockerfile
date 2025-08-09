# Multi-stage Dockerfile for Unifi Backup Container
# Optimized for production use with minimal attack surface

# Build stage
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set up build environment
WORKDIR /build

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    openssh-client \
    netcat-openbsd \
    iputils-ping \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r app && useradd -r -g app -u 1000 app

# Set up application directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Make sure scripts are executable
ENV PATH=/home/app/.local/bin:$PATH

# Copy application files
COPY backup_script.py .
COPY unifi_backup.py .
COPY json_converter.py .
COPY scheduler.py .
COPY entrypoint.sh .

# Create version file
RUN echo "1.0.0" > VERSION

# Set proper permissions
RUN chmod +x entrypoint.sh && \
    chown -R app:app /app

# Create backup directory and set permissions
RUN mkdir -p /app/backups && \
    chown -R app:app /app/backups

# Environment variables with defaults
ENV TZ=UTC \
    BACKUP_SCHEDULE=daily \
    BACKUP_TIME=02:00 \
    BACKUP_RETENTION_DAYS=30 \
    BACKUP_DIRECTORY=/app/backups \
    LOG_LEVEL=INFO \
    HEALTH_CHECK_PORT=8080 \
    UNIFI_PORT=22 \
    MAX_RETRIES=3 \
    RETRY_DELAY=60 \
    CONNECTION_TIMEOUT=30

# Expose health check port
EXPOSE 8080

# Configure volume for backup storage
VOLUME ["/app/backups"]

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER app

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command (scheduled mode)
CMD ["scheduled"]

# Labels for metadata
LABEL maintainer="Unifi Backup Container" \
      description="Automated Unifi network backup with JSON conversion" \
      version="1.0.0" \
      org.opencontainers.image.title="Unifi Backup Container" \
      org.opencontainers.image.description="Automated backup and JSON conversion for Unifi networks" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Unifi Documenter" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/loryanstrant/unifi-documenter"