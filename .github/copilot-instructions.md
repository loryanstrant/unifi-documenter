# Copilot instructions — unifi-documenter

> Canonical standards live in the `dev-standards` repo on SOUNDWAVE/Gitea.
> Read by Copilot chat **and** inline suggestions.

## What this repo is

A standalone **Dockerised Python web app** that documents UniFi network setups
(from backups), with AI-assisted analysis, embeddings, a scheduler, and an HTML
report/dashboard. Not a Home Assistant component.

## Repo shape

- `src/` — `main.py`, `web_server.py`, `backup_analyzer.py`, `backup_processor.py`,
  `ai_integration.py`, `embedding_manager.py`, `html_generator.py`,
  `scheduler.py`, `config.py`, `utils.py`, `version.py`.
- `templates/`, `static/`, `config/`, `output/` (`.gitkeep` placeholders).
- `Dockerfile`, `docker-compose.yml`, `docker-entrypoint.sh`, `run.sh`/`run.ps1`,
  `healthcheck.py`, `.env.template`, `.github/workflows/docker-build.yml`.

## Conventions

- Python web service: no `manifest.json`/`hassfest`/HACS.
- Versioned via `src/version.py`; CI builds the image.
- `fix_all_issues.py` looks like a one-off maintenance script — don't wire it into
  runtime.
- UniFi credentials + any AI API key go in `.env` (see `.env.template`) — never
  committed.

## Never

- Don't commit UniFi credentials, AI API keys, or network backups containing
  secrets.
