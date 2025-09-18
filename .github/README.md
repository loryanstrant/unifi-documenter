## UniFi Documenter

An intelligent Docker-based solution for automatically backing up, analyzing, and documenting UniFi Dream Machine configurations using AI.

### 🚀 Quick Start

```bash
# 1. Copy environment template
cp .env.template .env

# 2. Edit .env with your settings
# UDM_IP, UDM_ROOT_PASSWORD, AI_API_KEY, etc.

# 3. Start the service
docker-compose up -d
```

### 🔗 Links
- **Documentation**: [README.md](README.md)
- **Docker Image**: `ghcr.io/loryanstrant/unifi-documenter:latest`
- **Examples**: [examples.md](examples.md)
- **Setup Guide**: [GITHUB_SETUP.md](GITHUB_SETUP.md)

### ✨ Features
- AI-powered configuration analysis
- Supports OpenAI, Azure OpenAI, Ollama
- Automated scheduling with timezone support
- RAG-optimized markdown output
- Multi-architecture Docker images