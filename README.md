# UniFi Network Documentation Container

[![Build and Publish Docker Image](https://github.com/loryanstrant/unifi-documenter/actions/workflows/build.yml/badge.svg)](https://github.com/loryanstrant/unifi-documenter/actions/workflows/build.yml)
[![Docker Image Version](https://img.shields.io/docker/v/ghcr.io/loryanstrant/unifi-documenter?label=version)](https://github.com/loryanstrant/unifi-documenter/pkgs/container/unifi-documenter)
[![Docker Image Size](https://img.shields.io/docker/image-size/ghcr.io/loryanstrant/unifi-documenter?label=size)](https://github.com/loryanstrant/unifi-documenter/pkgs/container/unifi-documenter)

A comprehensive Docker container solution that automatically generates documentation for UniFi networks by connecting to the UniFi Network Controller API.

## Features

- **🔄 Automated Documentation**: Generates comprehensive documentation automatically
- **📅 Scheduled Runs**: Daily documentation generation at configurable times
- **🔒 Secure**: Runs as non-root user with proper authentication
- **🌐 Multi-Controller**: Support for multiple UniFi controllers
- **📊 Comprehensive Coverage**: Documents all aspects of your UniFi network
- **🐳 Containerized**: Ready-to-run Docker container
- **🏗️ Multi-Architecture**: Supports AMD64 and ARM64 platforms
- **💾 Backup Support**: Automatically backs up existing files with timestamps
- **🏥 Health Monitoring**: Built-in health checks and connectivity testing

## Quick Start

### Using Docker Run

```bash
# Basic usage with API key
docker run --rm -v $(pwd)/output:/output \
  -e UNIFI_CONTROLLER_IP=192.168.1.1 \
  -e UNIFI_API_KEY=your-api-key \
  ghcr.io/loryanstrant/unifi-documenter:latest --run-once

# Using username/password
docker run --rm -v $(pwd)/output:/output \
  -e UNIFI_CONTROLLER_IP=192.168.1.1 \
  -e UNIFI_USERNAME=admin \
  -e UNIFI_PASSWORD=your-password \
  ghcr.io/loryanstrant/unifi-documenter:latest --run-once
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  unifi-documenter:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    container_name: unifi-documenter
    restart: unless-stopped
    environment:
      - UNIFI_CONTROLLER_IP=192.168.1.1
      - UNIFI_API_KEY=your-api-key
      - UNIFI_TIMEZONE=America/New_York
      - UNIFI_SCHEDULE_TIME=02:00
    volumes:
      - ./unifi-docs:/output
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `UNIFI_CONTROLLER_IP` | IP address of UniFi controller | - | Yes* |
| `UNIFI_API_KEY` | API key for authentication | - | Yes* |
| `UNIFI_USERNAME` | Username for authentication | - | Yes* |
| `UNIFI_PASSWORD` | Password for authentication | - | Yes* |
| `UNIFI_VERIFY_SSL` | Enable/disable SSL certificate verification | `true` | No |
| `UNIFI_TIMEZONE` | Timezone for scheduling | `UTC` | No |
| `UNIFI_SCHEDULE_TIME` | Daily run time (HH:MM) | `02:00` | No |
| `UNIFI_OUTPUT_DIR` | Output directory | `/output` | No |
| `UNIFI_OUTPUT_FORMAT` | Output format (`markdown` or `json`) | `markdown` | No |
| `UNIFI_VERBOSE` | Enable verbose logging | `false` | No |

*Either API key OR username/password required

### Advanced Configuration

For multiple controllers or advanced settings, use a configuration file:

```yaml
# config.yml
unifi_controllers:
  - name: main
    host: 192.168.1.1
    api_key: your-api-key
  - name: remote
    host: 10.0.0.1
    username: admin
    password: password
    verify_ssl: false

unifi_timezone: America/New_York
unifi_schedule_time: "02:00"
output_format: markdown
```

Mount the config file:
```bash
docker run -v $(pwd)/config.yml:/app/config.yml \
  -v $(pwd)/output:/output \
  ghcr.io/loryanstrant/unifi-documenter:latest --config /app/config.yml
```

## Documentation Content

The generated documentation includes:

### 📊 **Networks & VLANs**
- All configured networks and VLAN assignments
- IP ranges and subnet configurations
- DHCP pool settings and static assignments

### 📡 **WiFi Networks**
- SSIDs and security settings
- VLAN assignments and guest networks
- WLAN groups and band configurations

### ⚙️ **Configuration Settings**
- Site settings and controller configurations
- Feature configurations and security policies
- System preferences and automation settings

### 👥 **Users & Clients**
- Connected clients and device information
- User groups and device assignments
- Known/configured clients with notes

### 🔧 **UniFi Devices**
- Access points, switches, and gateways
- Device details, status, and firmware versions
- Uptime and connection information

### 🌐 **IP Addressing**
- DHCP pools and static assignments
- Subnet configurations and routing
- DNS and domain settings

### 🔥 **Firewall Rules**
- Security policies and traffic rules
- Firewall groups and address sets
- Intrusion detection settings

### 🔀 **NAT Rules**
- Port forwarding configurations
- UPnP settings and policies
- Traffic routing rules

### 📈 **System Health & Statistics**
- Controller health status
- Network performance metrics
- DPI statistics and traffic analysis

## CLI Usage

The container provides a comprehensive CLI interface:

```bash
# Run as a service (default)
docker run ghcr.io/loryanstrant/unifi-documenter:latest

# Run documentation generation once
docker run ghcr.io/loryanstrant/unifi-documenter:latest --run-once

# Check service health
docker run ghcr.io/loryanstrant/unifi-documenter:latest --health

# Test connectivity to controllers
docker run ghcr.io/loryanstrant/unifi-documenter:latest --check-connectivity

# Enable verbose logging
docker run ghcr.io/loryanstrant/unifi-documenter:latest --verbose

# Show help
docker run ghcr.io/loryanstrant/unifi-documenter:latest --help
```

## Authentication Methods

### API Key (Recommended)

1. In UniFi Network Controller, go to **Settings** → **Admins**
2. Create a new admin or edit existing
3. Enable **Hotspot Manager** role (minimum required)
4. Generate an API key in the admin settings
5. Use the API key in your configuration

### Username/Password

Traditional username and password authentication is also supported:

```bash
docker run -e UNIFI_USERNAME=admin -e UNIFI_PASSWORD=your-password \
  ghcr.io/loryanstrant/unifi-documenter:latest
```

## Output Examples

### Markdown Output
- **Location**: `/output/unifi-{controller-name}-{timestamp}.md`
- **Latest**: `/output/unifi-{controller-name}-latest.md` (symlink)
- **Format**: Human-readable markdown with sections and tables

### JSON Output  
- **Location**: `/output/unifi-{controller-name}-{timestamp}.json`
- **Latest**: `/output/unifi-{controller-name}-latest.json` (symlink)
- **Format**: Structured JSON data for programmatic use

See [sample-output.md](sample-output.md) for a complete example.

## Health Monitoring

The container includes comprehensive health monitoring:

### Docker Health Checks
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' unifi-documenter
```

### Manual Health Checks
```bash
# Service health
docker exec unifi-documenter python main.py --health

# Controller connectivity
docker exec unifi-documenter python main.py --check-connectivity
```

### Health Check Responses

**Healthy**: All controllers configured and accessible  
**Degraded**: Some issues but service functional  
**Unhealthy**: Critical issues preventing operation

## Scheduling

The service runs on a configurable schedule:

- **Default**: Daily at 2:00 AM UTC
- **Configurable**: Use `UNIFI_SCHEDULE_TIME` (24-hour format)
- **Timezone Aware**: Set `UNIFI_TIMEZONE` for local time
- **Immediate**: Always runs once on startup

## File Management

### Backup Strategy
- Existing files are backed up with timestamps before new generation
- Format: `unifi-{controller}-backup-{timestamp}.{ext}`
- Symlinks always point to the latest files

### Directory Structure
```
/output/
├── unifi-main-20250720_140530.md          # Timestamped file
├── unifi-main-latest.md                   # Symlink to latest
├── unifi-main-backup-20250720_020000.md   # Previous backup
├── generation-status.txt                  # Last run status
└── ...
```

## Troubleshooting

### Common Issues

**No Controllers Configured**
```bash
# Check health to see configuration issues
docker run ghcr.io/loryanstrant/unifi-documenter:latest --health
```

**Authentication Failed**
```bash
# Test connectivity
docker run -e UNIFI_CONTROLLER_IP=192.168.1.1 -e UNIFI_API_KEY=test \
  ghcr.io/loryanstrant/unifi-documenter:latest --check-connectivity
```

**SSL Certificate Issues**
```yaml
# Option 1: Using config.yml
unifi_controllers:
  - name: main
    host: 192.168.1.1
    verify_ssl: false
    api_key: your-key
```

```bash
# Option 2: Using environment variable
docker run -e UNIFI_VERIFY_SSL=false -e UNIFI_CONTROLLER_IP=192.168.1.1 \
  -e UNIFI_API_KEY=your-key \
  ghcr.io/loryanstrant/unifi-documenter:latest --run-once
```

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
docker run -e UNIFI_VERBOSE=true \
  ghcr.io/loryanstrant/unifi-documenter:latest --run-once
```

## Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/loryanstrant/unifi-documenter.git
cd unifi-documenter

# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py --help
```

### Building Docker Image

```bash
# Build locally
docker build -t unifi-documenter .

# Multi-architecture build
docker buildx build --platform linux/amd64,linux/arm64 -t unifi-documenter .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with the UniFi Network Controller API
- Inspired by similar documentation tools
- Thanks to the UniFi community for API documentation and examples
