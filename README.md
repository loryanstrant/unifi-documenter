# UniFi Documenter

[![Docker Build](https://github.com/loryanstrant/unifi-documenter/actions/workflows/docker-build.yml/badge.svg)](https://github.com/loryanstrant/unifi-documenter/actions/workflows/docker-build.yml)
[![Docker Pulls](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/loryanstrant/unifi-documenter/pkgs/container/unifi-documenter)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An intelligent Docker-based solution for automatically backing up, analyzing, and documenting UniFi Dream Machine configurations using AI. This tool creates human-readable documentation with a modern web interface for real-time monitoring.

![UniFi Documenter Dashboard](docs/dashboard-screenshot.png)

## ✨ Features

### Core Capabilities
- 🔄 **Automated Scheduling**: Daily, weekly, or monthly backup processing
- 🤖 **AI-Powered Analysis**: Support for OpenAI, Azure OpenAI, Ollama, and custom APIs
- 🔑 **Flexible Authentication**: Optional API keys for local services, managed identities, and unauthenticated endpoints
- 🔍 **Enhanced Error Logging**: Detailed diagnostic information with URLs, error types, and troubleshooting hints
- 📚 **Smart Batch Processing**: Intelligent document grouping with 20x performance improvement
- 🐳 **Docker-Ready**: Complete containerized solution with multi-platform support (amd64/arm64)
- 🌍 **Timezone Support**: Configurable scheduling with timezone awareness
- 🔐 **Secure**: SSH-based backup retrieval with encrypted processing

### New Web Interface Features
- 🌐 **Real-time Dashboard**: Monitor analysis progress with live updates
- 📊 **Progress Tracking**: Visual progress bars showing document processing status
- 📁 **File Management**: View and download generated documentation directly from the web interface
- 📈 **Job History**: Track all analysis jobs with detailed statistics
- �� **Professional HTML Output**: Beautiful, responsive HTML documentation with modern styling
- 🔗 **Direct File Access**: Click to view or download any generated document

### Output Formats
- **HTML** (New!): Professional, styled documentation with syntax highlighting and responsive design
- **Markdown**: Traditional RAG-optimized markdown for search and analysis systems

## 🚀 Quick Start

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
```

### 3. Configure Environment Variables

Edit the `.env` file with your specific settings:

```bash
# UDM Configuration
UDM_IP=192.168.1.1
UDM_ROOT_PASSWORD=your_password_here

# AI Configuration (choose one provider)
AI_PROVIDER=openai

# API keys are now OPTIONAL - useful for:
# - Local Ollama (no API key needed)
# - OpenAI-compatible local endpoints (LM Studio, LocalAI)
# - Azure Managed Identity authentication
# - Network-level authentication
AI_API_KEY=your_openai_api_key_here

# Output Configuration
OUTPUT_FORMAT=html          # 'html' or 'markdown'
WEB_PORT=8080              # Web interface port

# Schedule Configuration
SCHEDULE_FREQUENCY=daily
SCHEDULE_TIME=02:00
TIMEZONE=America/New_York
```

### 4. Run with Docker Compose

```bash
# Start the service
docker-compose up -d

# Access the web interface
# Open http://localhost:8080 in your browser

# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

## 🌐 Web Interface

The web interface provides real-time monitoring and access to your documentation:

### Dashboard Features
- **Current Job Status**: See which documents are being processed in real-time
- **Progress Tracking**: Visual progress bars with document counts and batch information
- **Generated Files**: View list of generated files as they're created
- **Job History**: Review past analysis jobs with timestamps and statistics
- **Version Information**: Track the version and build of your running instance

### Accessing the Web Interface
By default, the web interface is available at `http://localhost:8080`. You can customize the port:

```yaml
# docker-compose.yml
ports:
  - "8090:8080"  # External port 8090, internal port 8080
```

Or via environment variable:
```bash
WEB_PORT=8090
```

### Security Considerations
The web interface is designed for local/internal network use. For production deployments, please review [README_SECURITY.md](README_SECURITY.md) for important security recommendations including:
- Network binding configuration
- Reverse proxy setup with authentication
- Access control best practices

## 📋 Configuration Options

### Output Configuration

```bash
# Output format: 'html' or 'markdown'
OUTPUT_FORMAT=html

# Maximum document size (default: 2MB)
MAX_DOCUMENT_SIZE=2000000

# Batch processing size
BATCH_SIZE=20

# Enable web interface (default: true)
WEB_ENABLED=true
WEB_PORT=8080
```

### Schedule Configuration

```bash
# Frequency: daily, weekly, monthly, manual
SCHEDULE_FREQUENCY=daily

# Time for scheduled runs (24-hour format)
SCHEDULE_TIME=02:00

# Your timezone
TIMEZONE=America/New_York

# Day of week (1=Monday, 7=Sunday) - for weekly schedules
SCHEDULE_DAY_OF_WEEK=1

# Day of month (1-31) - for monthly schedules
SCHEDULE_DAY_OF_MONTH=1
```

### AI Provider Configuration

#### OpenAI
```bash
AI_PROVIDER=openai
AI_API_KEY=sk-...          # Optional - can be omitted for local endpoints
AI_API_URL=https://api.openai.com/v1  # Optional - defaults to OpenAI
AI_MODEL=gpt-4o-mini
```

#### Azure OpenAI
```bash
AI_PROVIDER=azure-openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01
AI_API_KEY=your_key        # Optional - can use managed identity
```

**Azure Managed Identity**: Omit `AI_API_KEY` to use Azure Managed Identity authentication for secure, keyless access.

#### Ollama (Local AI - No API Key Required)
```bash
AI_PROVIDER=ollama
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:32b

# No API key needed - runs completely local
# Recommended models for documentation:
# - qwen2.5:32b (Best quality, slower)
# - llama3.1:8b (Good balance)
# - phi3.5:latest (Fastest, smaller)
```

#### Custom OpenAI-Compatible API
```bash
AI_PROVIDER=custom
AI_API_URL=https://your-api.com/v1
AI_MODEL=your-model
AI_API_KEY=your_key        # Optional - omit if endpoint doesn't require auth

# Works with:
# - LM Studio (http://localhost:1234/v1)
# - LocalAI (http://localhost:8080/v1)
# - vLLM (http://localhost:8000/v1)
# - Any OpenAI-compatible endpoint
```

### Authentication Options

API keys are now **optional** for all providers, enabling:

1. **Local Services**: Run Ollama or other local models without any API keys
2. **Network Authentication**: Use internal APIs with network-level authentication
3. **Managed Identity**: Azure resources can authenticate without storing keys
4. **Development/Testing**: Test configurations safely without real API keys
5. **OpenAI-Compatible Endpoints**: Use LM Studio, LocalAI, or similar local services

## 🔍 Enhanced Error Logging

The application now provides detailed diagnostic information for troubleshooting AI provider issues:

### What's Logged

**Connection Issues:**
```
ERROR - Ollama provider unavailable: Connection error to http://localhost:11434
ERROR - Required: OLLAMA_URL (current: http://localhost:11434), OLLAMA_MODEL (current: llama3)
ERROR - Ensure Ollama is running and accessible at the configured URL
```

**Configuration Problems:**
```
ERROR - AI provider 'custom' is not available
ERROR - Required: AI_API_URL (current: https://api.example.com/v1), AI_MODEL (current: gpt-4)
ERROR - Optional: AI_API_KEY (configured: No)
```

**API Errors:**
```
ERROR - OpenAI API error: Invalid API key
ERROR - API URL: https://api.openai.com/v1
ERROR - Model: gpt-4o-mini
ERROR - Error type: AuthenticationError
```

### Benefits

- **Exact URLs and Endpoints**: See exactly which endpoints are being accessed
- **Current Configuration Values**: View your actual configuration without revealing secrets
- **Error Type Classification**: Understand if it's a connection, authentication, or API issue
- **Provider-Specific Hints**: Get tailored troubleshooting advice for your AI provider
- **HTTP Response Details**: See status codes and response bodies for API failures

This makes troubleshooting much easier without needing to modify code or add debug statements.

## 📊 Performance

### Batch Processing Performance
- **Before**: 730 documents in ~2.5 hours (sequential processing)
- **After**: 730 documents in ~18 minutes (batch processing with smart grouping)
- **Improvement**: ~8.3x faster processing time

### Smart Document Grouping
Documents are automatically grouped by type for efficient batch processing:
- **Devices**: Switches, access points, gateways
- **Networks**: VLANs, subnets, routing configurations  
- **Firewall**: Rules, port forwarding, security policies
- **Wireless**: SSIDs, wireless networks, radio settings
- **Ports**: Port configurations and profiles
- **Users**: User accounts and authentication
- **Settings**: System settings and preferences

## 🐳 Docker Images

### Pre-built Images
The latest images are available on GitHub Container Registry:

```bash
# Latest stable release
docker pull ghcr.io/loryanstrant/unifi-documenter:latest

# Specific version (when available)
docker pull ghcr.io/loryanstrant/unifi-documenter:v1.0.0
```

### Multi-Platform Support
Images are built for both:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/v8)

### Using Pre-built Images
Update your `docker-compose.yml` to use the pre-built image:

```yaml
services:
  unifi-documenter:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    # Remove the 'build: .' line when using pre-built images
    ports:
      - "8080:8080"
    volumes:
      - ./backups:/app/backups
      - ./output:/app/output
    env_file:
      - .env
```

## 📁 Directory Structure

```
unifi-documenter/
├── backups/          # UniFi backup files (*.unf)
├── output/           # Generated documentation (HTML/Markdown)
├── logs/             # Application logs
├── src/              # Source code
│   ├── backup_analyzer.py    # Core analysis with batch processing
│   ├── web_server.py         # Flask web interface
│   ├── html_generator.py     # HTML output generation
│   ├── markdown_generator.py # Markdown output generation
│   ├── ai_documenter.py      # AI provider integration
│   ├── config.py             # Configuration management
│   └── version.py            # Version tracking
├── templates/        # HTML templates for web interface
├── static/          # Static assets (CSS, images)
├── docker-compose.yml
├── Dockerfile
├── .env.template
└── README.md
```

## 🔧 Manual Backup Processing

To manually process a backup without scheduling:

```bash
# Copy your backup file to the backups directory
cp /path/to/backup.unf ./backups/

# Set schedule to manual mode
echo "SCHEDULE_FREQUENCY=manual" >> .env

# Restart container
docker-compose restart

# Monitor progress in web interface
# Or check logs
docker-compose logs -f
```

## 📖 Generated Documentation

### HTML Output (New!)
- Professional styling with gradient headers and responsive design
- Syntax-highlighted code blocks and formatted tables
- Metadata cards showing configuration details
- Cross-references between related documents
- Batch reports with statistics and document summaries

### Markdown Output
- Structured with clear headers and sections
- Optimized for RAG (Retrieval-Augmented Generation)
- Includes metadata and cross-references
- Easy to search and index

### Example Output Structure
```
output/
├── devices_a1b2c3d4.html          # Individual device config
├── networks_e5f6g7h8.html         # Network configuration
├── firewall_i9j0k1l2.html         # Firewall rules
├── batch_devices_2026-01-05.html  # Batch report for devices
└── ...
```

## 🔍 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs

# Verify .env file
cat .env | grep -v '^#' | grep -v '^$'

# Check permissions
chmod 755 backups output logs
```

**Web interface not accessible:**
```bash
# Check if port is available
netstat -an | grep 8080

# Check container is running
docker-compose ps

# Verify port mapping
docker-compose port unifi-documenter 8080
```

**Backup processing fails:**
```bash
# Verify UDM connection
ssh root@${UDM_IP} 'ls -la /data/autobackup/'

# Review logs for detailed error information
docker-compose logs | grep ERROR

# The enhanced error logging will show:
# - Exact URLs and endpoints being accessed
# - Current configuration values
# - Specific error types (ConnectionError, AuthenticationError, etc.)
# - Provider-specific troubleshooting hints
```

**AI Provider Issues:**

The application now provides detailed diagnostics. Check logs for:

1. **Configuration Problems**: Missing or incorrect API URLs, endpoints, or models
   - Look for: "Required: AI_API_URL (current: ...)"
   - Look for: "Optional: AI_API_KEY (configured: Yes/No)"

2. **Connection Errors**: Network issues or wrong URLs
   - Look for: "Connection error to http://localhost:11434"
   - Verify the endpoint is accessible from within the Docker container

3. **Authentication Failures**: Invalid or missing API keys (when required)
   - Look for: "Error type: AuthenticationError"
   - Verify API key is correct and has necessary permissions

4. **API Errors**: Service-specific issues
   - Look for HTTP status codes and response bodies
   - Check provider's status page for outages

**Example Error Messages:**
```
ERROR - AI provider 'ollama' is not available
ERROR - Required: OLLAMA_URL (current: http://localhost:11434), OLLAMA_MODEL (current: llama3)
ERROR - Ensure Ollama is running and accessible at the configured URL
DEBUG - Ollama provider unavailable: Connection error to http://localhost:11434 - [Errno 111] Connection refused
```

**Large files truncated:**
- Default limit is 2MB per document
- Adjust `MAX_DOCUMENT_SIZE` in .env if needed
- Check logs for truncation warnings

## 📈 Resource Usage

### Recommended Resources
- **CPU**: 2 cores minimum
- **RAM**: 2GB minimum
- **Disk**: 1GB + space for output files
- **Network**: Stable connection to UDM and AI provider

### Container Limits
Default limits (can be adjusted in docker-compose.yml):
```yaml
resources:
  limits:
    cpus: '2'
    memory: 2G
    pids: 200
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

For security considerations regarding the web interface, please review [README_SECURITY.md](README_SECURITY.md).

To report security vulnerabilities, please email security@yourdomain.com instead of using the issue tracker.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/loryanstrant/unifi-documenter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/loryanstrant/unifi-documenter/discussions)
- **Documentation**: [Wiki](https://github.com/loryanstrant/unifi-documenter/wiki)

## 🙏 Acknowledgments

- Built with Python, Flask, and Docker
- AI documentation powered by OpenAI, Azure, and Ollama
- Inspired by the UniFi community's need for better documentation tools

---

**Version**: 1.0.0 | **Build**: 2026.01.05
