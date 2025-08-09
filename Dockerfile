FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-client \
    git \
    cron \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application files
COPY backup.py .
COPY decrypt_backup.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create directories
RUN mkdir -p /backups/latest /backups/archives /app/logs

# Create a non-root user
RUN useradd -m -u 1000 unifi && \
    chown -R unifi:unifi /app /backups
USER unifi

# Set up Git config
RUN git config --global user.name "UniFi Documenter" && \
    git config --global user.email "unifi-documenter@localhost" && \
    git config --global init.defaultBranch main

# Expose volume for backups
VOLUME ["/backups"]

# Default entrypoint
ENTRYPOINT ["./entrypoint.sh"]