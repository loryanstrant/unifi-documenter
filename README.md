# Unifi Network Backup Container

A comprehensive Docker container solution for automated Unifi network backup with JSON conversion. This container connects to your Unifi Dream Machine, switches, and access points via SSH to download, decrypt, and convert backup files into structured JSON format.

## Features

- **Automated Backup**: SSH-based backup download from Unifi controllers
- **Decryption Support**: Handles encrypted .unf backup files
- **JSON Conversion**: Converts all backup data into structured JSON files
- **Flexible Scheduling**: Daily, weekly, or custom cron-based scheduling
- **Version Control**: Timestamped backups with configurable retention
- **Health Monitoring**: Built-in health checks and monitoring endpoints
- **Security Focused**: Runs as non-root user with minimal attack surface
- **Multi-Architecture**: Supports both AMD64 and ARM64 platforms

## Quick Start

### Using Docker Compose (Recommended)

1. Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  unifi-backup:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    container_name: unifi-backup
    restart: unless-stopped
    environment:
      UNIFI_HOST: "192.168.1.1"
      UNIFI_USERNAME: "root"
      UNIFI_PASSWORD: "your-password"
      BACKUP_SCHEDULE: "daily"
      BACKUP_TIME: "02:00"
      TZ: "America/New_York"
    volumes:
      - ./backups:/app/backups
    ports:
      - "8080:8080"
```

2. Start the container:

```bash
docker-compose up -d
```

### Using Docker CLI

```bash
docker run -d \
  --name unifi-backup \
  --restart unless-stopped \
  -e UNIFI_HOST=192.168.1.1 \
  -e UNIFI_USERNAME=root \
  -e UNIFI_PASSWORD=your-password \
  -e BACKUP_SCHEDULE=daily \
  -e BACKUP_TIME=02:00 \
  -e TZ=America/New_York \
  -v ./backups:/app/backups \
  -p 8080:8080 \
  ghcr.io/loryanstrant/unifi-documenter:latest
```

## Configuration

### Environment Variables

#### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `UNIFI_HOST` | IP address of the Unifi controller | `192.168.1.1` |
| `UNIFI_USERNAME` | SSH username for controller access | `root` |
| `UNIFI_PASSWORD` | SSH password for controller access | `your-password` |

#### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UNIFI_PORT` | `22` | SSH port for controller access |
| `TZ` | `UTC` | Timezone for scheduling |
| `BACKUP_SCHEDULE` | `daily` | Schedule frequency (`daily`, `weekly`, or `cron:expression`) |
| `BACKUP_TIME` | `02:00` | Time of day to run backup (HH:MM format) |
| `BACKUP_RETENTION_DAYS` | `30` | Number of days to retain backups |
| `BACKUP_DIRECTORY` | `/app/backups` | Directory to store backups |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARN`, `ERROR`) |
| `HEALTH_CHECK_PORT` | `8080` | Port for health check endpoint |
| `MAX_RETRIES` | `3` | Maximum retry attempts for failed operations |
| `RETRY_DELAY` | `60` | Delay between retries (seconds) |
| `CONNECTION_TIMEOUT` | `30` | SSH connection timeout (seconds) |

### Advanced Scheduling

For custom scheduling, use the `cron:` prefix with a standard cron expression:

```bash
# Every 6 hours
BACKUP_SCHEDULE="cron:0 */6 * * *"

# Every Monday at 3 AM
BACKUP_SCHEDULE="cron:0 3 * * 1"

# First day of every month at midnight
BACKUP_SCHEDULE="cron:0 0 1 * *"
```

## Usage Modes

### Scheduled Mode (Default)

The container runs continuously and performs backups according to the schedule:

```bash
docker run [...] ghcr.io/loryanstrant/unifi-documenter:latest
# or
docker run [...] ghcr.io/loryanstrant/unifi-documenter:latest scheduled
```

### One-Time Backup

Run a single backup operation and exit:

```bash
docker run --rm [...] ghcr.io/loryanstrant/unifi-documenter:latest once
```

### Connection Test

Test SSH connectivity without performing a backup:

```bash
docker run --rm [...] ghcr.io/loryanstrant/unifi-documenter:latest test
```

## Backup Output Structure

The container creates organized backup directories with the following structure:

```
backups/
├── backup_20231215_143022/          # Timestamped backup directory
│   ├── original_backup.unf          # Original backup file
│   ├── device_info.json             # Controller device information
│   └── json_20231215_143022/        # Converted JSON files
│       ├── sites.json               # Site configurations
│       ├── devices.json             # Device configurations
│       ├── networks.json            # Network settings
│       ├── users.json               # User/client data
│       ├── settings.json            # System settings
│       ├── complete_backup.json     # Complete backup data
│       └── summary.json             # Conversion summary
└── .scheduler_state.json            # Scheduler state (internal)
```

### JSON File Contents

- **sites.json**: Site configurations, VLANs, and network policies
- **devices.json**: Access points, switches, and other Unifi devices
- **networks.json**: Network configurations, SSIDs, and wireless settings
- **users.json**: Client devices and user information
- **settings.json**: System-wide configuration settings
- **complete_backup.json**: All data combined in a structured format
- **summary.json**: Metadata about the backup and conversion process

## Monitoring and Health Checks

### Health Check Endpoint

The container exposes a health check endpoint at `http://localhost:8080/health`:

```bash
curl http://localhost:8080/health
```

Response example:
```json
{
  "status": "healthy",
  "timestamp": "2023-12-15T14:30:22.123456",
  "config": {
    "unifi_host": "192.168.1.1",
    "backup_schedule": "daily",
    "backup_time": "02:00",
    "backup_directory": "/app/backups"
  },
  "last_backup": "2023-12-15T02:00:15.789123",
  "next_backup": "2023-12-16T02:00:00.000000"
}
```

### Docker Health Checks

The container includes built-in Docker health checks:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Logs

View container logs:

```bash
# Follow logs
docker logs -f unifi-backup

# View recent logs
docker logs --tail 100 unifi-backup
```

## Security Considerations

### Container Security

- Runs as non-root user (UID 1000)
- Minimal base image with only required dependencies
- No unnecessary ports exposed
- Secure handling of credentials through environment variables

### Network Security

- SSH connections use password authentication (consider SSH keys for production)
- No persistent SSH connections maintained
- Configurable connection timeouts and retry limits

### Data Security

- Backup files are stored locally and not transmitted elsewhere
- Credentials are only used for SSH authentication
- Automatic cleanup of old backups based on retention policy

### Recommendations

1. **Use SSH Keys**: For production environments, consider using SSH key authentication instead of passwords
2. **Network Isolation**: Run the container in a dedicated network or VLAN
3. **Backup Encryption**: Consider encrypting the backup storage volume
4. **Regular Updates**: Keep the container image updated for security patches

## Troubleshooting

### Common Issues

#### SSH Connection Failed

```bash
# Test SSH connectivity manually
ssh root@192.168.1.1

# Check SSH port
nc -zv 192.168.1.1 22

# Verify credentials
docker run --rm [...] ghcr.io/loryanstrant/unifi-documenter:latest test
```

#### Backup Decryption Failed

```bash
# Check if .unf file is actually encrypted
file /path/to/backup.unf

# Try manual extraction
unzip -t /path/to/backup.unf
```

#### Permission Issues

```bash
# Check volume permissions
ls -la ./backups/

# Fix permissions (if needed)
sudo chown -R 1000:1000 ./backups/
```

### Debug Mode

Enable debug logging for troubleshooting:

```yaml
environment:
  LOG_LEVEL: "DEBUG"
```

### Container Logs

The container provides structured JSON logging for easy parsing and monitoring:

```bash
docker logs unifi-backup | jq '.'
```

## Development

### Building Locally

```bash
# Clone the repository
git clone https://github.com/loryanstrant/unifi-documenter.git
cd unifi-documenter

# Build the container
docker build -t unifi-backup:local .

# Run with local image
docker run [...] unifi-backup:local
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Testing

```bash
# Run linting
flake8 *.py

# Format code
black *.py

# Sort imports
isort *.py

# Test container build
docker build --no-cache .
```

## Supported Devices

This container has been tested with:

- Unifi Dream Machine (UDM)
- Unifi Dream Machine Pro (UDM-Pro)
- Unifi Dream Machine SE (UDM-SE)
- Unifi Cloud Key Gen2
- Self-hosted Unifi Network Controller

## Examples

### Multiple Controllers

Monitor multiple Unifi controllers:

```yaml
version: '3.8'

services:
  unifi-backup-main:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    environment:
      UNIFI_HOST: "192.168.1.1"
      UNIFI_USERNAME: "root"
      UNIFI_PASSWORD: "password1"
      BACKUP_TIME: "02:00"
    volumes:
      - ./backups/main:/app/backups
    ports:
      - "8081:8080"

  unifi-backup-remote:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    environment:
      UNIFI_HOST: "192.168.2.1"
      UNIFI_USERNAME: "root"
      UNIFI_PASSWORD: "password2"
      BACKUP_TIME: "03:00"
    volumes:
      - ./backups/remote:/app/backups
    ports:
      - "8082:8080"
```

### Custom Scheduling

Weekly backups on Sundays:

```yaml
environment:
  BACKUP_SCHEDULE: "weekly"
  BACKUP_TIME: "01:00"
```

Custom cron schedule (every 4 hours):

```yaml
environment:
  BACKUP_SCHEDULE: "cron:0 */4 * * *"
```

### Resource Limits

For resource-constrained environments:

```yaml
deploy:
  resources:
    limits:
      memory: 256M
      cpus: '0.25'
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: Report bugs and feature requests on [GitHub Issues](https://github.com/loryanstrant/unifi-documenter/issues)
- **Documentation**: This README and inline code documentation
- **Community**: Discussions on GitHub Discussions (if enabled)

## Changelog

### v1.0.0

- Initial release
- Automated Unifi backup with SSH support
- JSON conversion of backup files
- Flexible scheduling with cron support
- Health monitoring and logging
- Multi-architecture Docker images
- Comprehensive documentation