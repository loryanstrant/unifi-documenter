# UniFi Documenter

[![Docker Build](https://github.com/loryanstrant/unifi-documenter/actions/workflows/docker-build.yml/badge.svg)](https://github.com/loryanstrant/unifi-documenter/actions/workflows/docker-build.yml)
[![Docker Pulls](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/loryanstrant/unifi-documenter/pkgs/container/unifi-documenter)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An intelligent Docker-based solution for automatically backing up, analyzing, and documenting UniFi Dream Machine configurations using AI. This tool creates human-readable and RAG-optimized markdown documentation from UniFi backup files.

## Features

- 🔄 **Automated Scheduling**: Daily, weekly, or monthly backup processing
- 🤖 **AI-Powered Analysis**: Support for OpenAI, Azure OpenAI, Ollama, and custom APIs
- 📚 **RAG-Optimized Output**: Structured markdown perfect for RAG systems
- 🐳 **Docker-Ready**: Complete containerized solution
- 🌍 **Timezone Support**: Configurable scheduling with timezone awareness
- 📊 **Comprehensive Documentation**: Detailed analysis with summaries and indexes
- 🔐 **Secure**: SSH-based backup retrieval with encrypted processing

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/loryanstrant/unifi-documenter.git
cd unifi-documenter

# Copy and edit environment configuration
cp .env.template .env
# Edit .env with your settings
```

### 2. Use Pre-built Image (Recommended)

```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/loryanstrant/unifi-documenter:latest

# Or use docker-compose with the pre-built image
# (update docker-compose.yml to use: image: ghcr.io/loryanstrant/unifi-documenter:latest)
```

### 3. Configure Environment Variables

Edit the `.env` file with your specific settings:

```bash
# UDM Configuration
UDM_IP=192.168.1.1
UDM_ROOT_PASSWORD=your_password_here

# AI Configuration (choose one)
AI_PROVIDER=openai
AI_API_KEY=your_openai_api_key_here

# Schedule Configuration
SCHEDULE_FREQUENCY=daily
SCHEDULE_TIME=02:00
TIMEZONE=America/New_York
```

### 4. Run with Docker Compose

```bash
# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

## Docker Images

### Pre-built Images
The latest images are available on GitHub Container Registry:

```bash
# Latest stable release
docker pull ghcr.io/loryanstrant/unifi-documenter:latest

# Specific version (when available)
docker pull ghcr.io/loryanstrant/unifi-documenter:v1.0.0
```

### Using Pre-built Images
Update your `docker-compose.yml` to use the pre-built image:

```yaml
services:
  unifi-documenter:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    # Remove the 'build: .' line when using pre-built images
```

## Configuration Options

### Schedule Configuration

| Variable | Options | Description |
|----------|---------|-------------|
| `SCHEDULE_FREQUENCY` | `daily`, `weekly`, `monthly` | How often to run |
| `SCHEDULE_TIME` | `HH:MM` (24-hour) | When to run |
| `SCHEDULE_DAY` | 1-7 (weekly), 1-31 (monthly) | Which day to run |
| `TIMEZONE` | IANA timezone | Timezone for scheduling |

### UDM Configuration

| Variable | Description |
|----------|-------------|
| `UDM_IP` | IP address of your UniFi Dream Machine |
| `UDM_ROOT_PASSWORD` | Root password for SSH access |
| `REMOTE_BACKUP_DIR` | Directory containing backup files |

### AI Provider Configuration

#### OpenAI (Default)
```bash
AI_PROVIDER=openai
AI_API_URL=https://api.openai.com/v1
AI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4o-mini
```

#### Azure OpenAI
```bash
AI_PROVIDER=azure-openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment
AZURE_OPENAI_API_VERSION=2024-02-01
AI_API_KEY=your_azure_key
```

#### Ollama (Local/Self-hosted)
```bash
AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
# Or for Docker: OLLAMA_URL=http://host.docker.internal:11434
# Or remote: OLLAMA_URL=http://your-ollama-server:11434
OLLAMA_MODEL=llama3
```

#### Custom OpenAI-Compatible API
```bash
AI_PROVIDER=custom
AI_API_URL=https://your-api-endpoint.com/v1
AI_API_KEY=your_api_key
AI_MODEL=your_model_name
```

**Note**: Each AI provider uses different endpoint configuration variables. The system automatically selects the correct endpoint based on the `AI_PROVIDER` setting.

## Output Structure

The system generates organized documentation in the `/output` directory:

```
output/
└── unifi-backup-2024-01-15-02-00/
    ├── decrypted.zip                 # Decrypted backup file
    ├── extracted/                    # Raw extracted data
    ├── db.json                      # Full database in JSON
    ├── json_documents/              # Individual JSON documents
    └── analysis/                    # AI-generated documentation
        ├── INDEX.md                 # Master index
        ├── SUMMARY.md              # Overall analysis
        ├── doc_abc12345.md         # Individual config docs
        └── doc_def67890.md
```

### Documentation Features

- **Structured Markdown**: Clean, searchable format
- **Metadata Frontmatter**: YAML metadata for each document
- **Cross-References**: Linked navigation between documents
- **RAG Optimization**: Formatted for retrieval systems
- **Configuration Summaries**: High-level overviews
- **Searchable Content**: Keyword-rich descriptions

## Running Modes

### Scheduled Mode (Default)
Runs continuously and processes backups on schedule:
```bash
docker-compose up -d
```

### One-Time Execution
Process backup once and exit:
```bash
docker run --rm -e RUN_MODE=once \
  --env-file .env \
  -v ./output:/app/output \
  unifi-documenter
```

### Manual Trigger
Run immediately on startup, then continue on schedule:
```bash
docker-compose run -e RUN_IMMEDIATELY=true unifi-documenter
```

## Monitoring

### Health Checks
The container includes built-in health checks:
```bash
docker-compose ps  # Shows health status
```

### Logs
View application logs:
```bash
# Container logs
docker-compose logs -f unifi-documenter

# Application log file
tail -f output/unifi-documenter.log
```

### Status Information
Check scheduler status and next run time in the logs.

## Advanced Configuration

### Custom AI Models

For specialized analysis, configure custom models:
```bash
AI_MODEL=gpt-4-turbo-preview  # For more detailed analysis
# or
AI_MODEL=gpt-3.5-turbo       # For faster, cost-effective processing
```

### Output Customization

```bash
OUTPUT_FORMAT=markdown        # markdown, json, both
MAX_DOCUMENT_SIZE=50000      # Characters per document
INCLUDE_RAW_DATA=true        # Include original JSON
```

### Network Configuration

For custom network setups:
```yaml
# docker-compose.yml
networks:
  unifi-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Troubleshooting

### Common Issues

#### SSH Connection Failed
- Verify UDM IP address and credentials
- Ensure SSH is enabled on UDM
- Check firewall settings

#### AI API Errors
- Verify API key and endpoint
- Check model availability
- Monitor rate limits

#### No Backup Files Found
- Verify backup directory path
- Check UDM backup settings
- Ensure automatic backups are enabled

#### Permission Issues
```bash
# Fix output directory permissions
sudo chown -R 1000:1000 output/
```

### Debug Mode

Enable verbose logging:
```bash
docker-compose run -e LOG_LEVEL=DEBUG unifi-documenter
```

### Testing Configuration

Test without scheduling:
```bash
docker-compose run -e RUN_MODE=once unifi-documenter
```

## Security Considerations

- Store credentials securely (use Docker secrets in production)
- Regularly rotate UDM passwords
- Secure AI API keys
- Monitor log files for sensitive data
- Use least-privilege access for UDM

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python src/main.py
```

### Building Custom Images

```bash
# Build image
docker build -t unifi-documenter:custom .

# Use custom image
# Update docker-compose.yml to use custom image
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Check the troubleshooting section
- Review logs for error details
- Open an issue with detailed information

---

**Note**: This tool requires SSH access to your UniFi Dream Machine and appropriate API access for your chosen AI provider. Ensure you have the necessary permissions and credentials before deployment.