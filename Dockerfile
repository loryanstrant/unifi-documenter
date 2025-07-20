FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including timezone data and cron
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY main.py .

# Create output directory
RUN mkdir -p /output

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app /output

USER app

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Service-specific environment variables with defaults
ENV UNIFI_OUTPUT_DIR=/output
ENV UNIFI_TIMEZONE=UTC
ENV UNIFI_SCHEDULE_TIME=02:00
ENV UNIFI_OUTPUT_FORMAT=markdown

# Health check - check if the service is responsive
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python main.py --health || exit 1

# Default command - start the service
ENTRYPOINT ["python", "main.py"]