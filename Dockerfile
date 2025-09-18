FROM python:3.11-slim

# Install system dependencies including gosu for user switching
RUN apt-get update && apt-get install -y \
    openssh-client \
    sshpass \
    openssl \
    unzip \
    gzip \
    jq \
    mongodb-clients \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY healthcheck.py ./
COPY docker-entrypoint.sh ./

# Make scripts executable
RUN chmod +x docker-entrypoint.sh healthcheck.py

# Create output directory
RUN mkdir -p /app/output

# Set environment variables
ENV PYTHONPATH="/app"
ENV TZ=UTC

# Create a non-root user
RUN useradd -m -u 1000 unifi-user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python healthcheck.py

# Default command
ENTRYPOINT ["./docker-entrypoint.sh"]