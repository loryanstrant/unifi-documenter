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
# Basic usage with username/password
docker run --rm -v $(pwd)/output:/output \
  -e UNIFI_CONTROLLER_URL=https://unifi.example.com:8443 \
  -e UNIFI_USERNAME=your_local_admin_user \
  -e UNIFI_PASSWORD=your_password \
  ghcr.io/loryanstrant/unifi-documenter:latest --run-once

# For UDM Pro controllers (port 443)
docker run --rm -v $(pwd)/output:/output \
  -e UNIFI_CONTROLLER_URL=https://unifi.example.com:443 \
  -e UNIFI_USERNAME=your_local_admin_user \
  -e UNIFI_PASSWORD=your_password \
  -e UNIFI_IS_UDM_PRO=true \
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
      - UNIFI_CONTROLLER_URL=https://unifi.example.com:8443
      - UNIFI_USERNAME=your_local_admin_user
      - UNIFI_PASSWORD=your_password
      - UNIFI_IS_UDM_PRO=false
      - UNIFI_TIMEZONE=America/New_York
      - UNIFI_SCHEDULE_TIME=02:00
    volumes:
      - ./unifi-docs:/output
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `UNIFI_CONTROLLER_URL` | Full URL of UniFi controller (e.g., https://unifi.example.com:8443) | - | Yes |
| `UNIFI_USERNAME` | Local admin username for authentication | - | Yes |
| `UNIFI_PASSWORD` | Password for authentication | - | Yes |
| `UNIFI_IS_UDM_PRO` | Set to true for UniFi OS based controllers | `false` | No |
| `UNIFI_API_VERSION` | UniFi API version (auto-detected if not specified) | `auto` | No |
| `UNIFI_VERIFY_SSL` | Verify SSL certificates | `true` | No |
| `UNIFI_TIMEZONE` | Timezone for scheduling | `UTC` | No |
| `UNIFI_SCHEDULE_TIME` | Daily run time (HH:MM) | `02:00` | No |
| `UNIFI_OUTPUT_DIR` | Output directory | `/output` | No |
| `UNIFI_OUTPUT_FORMAT` | Output format (`markdown` or `json`) | `markdown` | No |
| `UNIFI_VERBOSE` | Enable verbose logging | `false` | No |

### Advanced Configuration

For multiple controllers or advanced settings, use a configuration file:

```yaml
# config.yml
unifi_controllers:
  - name: main
    controller_url: "https://unifi.example.com:8443"
    username: your_local_admin_user
    password: your_password
    is_udm_pro: false
    verify_ssl: true
    api_version: v5  # Optional: specify API version (auto-detected if omitted)
  - name: remote
    controller_url: "https://remote.example.com:443"
    username: admin
    password: your_password
    is_udm_pro: true
    verify_ssl: false
    api_version: unifiOS  # Optional: force specific API version for UDM Pro

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

## Authentication

The UniFi documenter uses the established `pyunifi` library for connecting to UniFi Controllers. It supports username and password authentication only.

### Username/Password Authentication

Standard authentication using a local UniFi admin account:

```bash
docker run -e UNIFI_CONTROLLER_URL=https://unifi.example.com:8443 \
  -e UNIFI_USERNAME=admin \
  -e UNIFI_PASSWORD=your-password \
  ghcr.io/loryanstrant/unifi-documenter:latest
```

### UDM Pro Configuration

For UniFi OS based controllers (UDM Pro, UDM SE, etc.), set the `is_udm_pro` parameter:

```bash
docker run -e UNIFI_CONTROLLER_URL=https://unifi.example.com:443 \
  -e UNIFI_USERNAME=admin \
  -e UNIFI_PASSWORD=your-password \
  -e UNIFI_IS_UDM_PRO=true \
  ghcr.io/loryanstrant/unifi-documenter:latest
```

### SSL Certificate Configuration

You can control SSL certificate verification:

```bash
# Disable SSL verification (self-signed certificates)
-e UNIFI_VERIFY_SSL=false

# Custom CA bundle (mount the file and specify path)
-v /path/to/ca-bundle.pem:/certs/ca-bundle.pem:ro
-e UNIFI_VERIFY_SSL=/certs/ca-bundle.pem
```

### API Version Configuration

The UniFi Documenter automatically detects the correct API version for your controller. However, you can override this behavior for specific situations:

#### Automatic Detection (Recommended)

By default, the application will try multiple API versions in this order:
1. Specified version (if `UNIFI_API_VERSION` is set)
2. `v5` (most common)
3. `unifiOS` (for UDM Pro/SE controllers)
4. `v4` (older controllers)
5. `v6` (newer controllers)

#### Manual Override

```bash
# Force a specific API version
-e UNIFI_API_VERSION=unifiOS

# For UDM Pro controllers having authentication issues
-e UNIFI_API_VERSION=unifiOS
-e UNIFI_IS_UDM_PRO=true

# For older controllers
-e UNIFI_API_VERSION=v4
```

#### Configuration File API Version

```yaml
unifi_controllers:
  - name: legacy
    controller_url: "https://old-unifi.example.com:8443"
    username: admin
    password: password
    api_version: v4  # Force v4 for legacy controller
  - name: udm-pro
    controller_url: "https://udm.example.com"
    username: admin
    password: password
    is_udm_pro: true
    api_version: unifiOS  # Force unifiOS for UDM Pro
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
docker run -e UNIFI_CONTROLLER_URL=https://unifi.example.com:8443 \
  -e UNIFI_USERNAME=admin -e UNIFI_PASSWORD=test \
  ghcr.io/loryanstrant/unifi-documenter:latest --check-connectivity
```

**SSL Certificate Issues**
```yaml
# Disable SSL verification in config
unifi_controllers:
  - name: main
    controller_url: "https://unifi.example.com:8443"
    username: admin
    password: your_password
    verify_ssl: false
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

- Built with the [pyunifi](https://github.com/finish06/pyunifi) library for UniFi Controller API access
- Follows the TNWare UniFi Controller API documentation configuration format
- Thanks to the UniFi community for API documentation and examples
