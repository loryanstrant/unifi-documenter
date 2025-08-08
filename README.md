# Unifi Documenter

## Overview
This project provides a Dockerized solution for scheduled backups of Unifi configurations, along with JSON conversion and version control features.

## Features
- Dockerized scheduled backups
- JSON conversion of backup files
- Version control for backup files
- GitHub Container Registry (GHCR) workflow

## Usage
1. Set up your `.env` file based on the `.env.example` provided.
2. Build and run the Docker container:
   ```bash
   docker-compose up -d
   ```
3. The scheduled backups will run as per the configuration in `docker-compose.yml`.

## Contributing
Please feel free to fork the repository and submit pull requests for any improvements.