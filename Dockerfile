# Dockerfile for Unifi Documenter

FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the entry point
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
