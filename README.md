# UniFi Documenter

A comprehensive Docker container that automatically backs up, decrypts, and documents UniFi network configurations. This tool connects to UniFi Dream Machines and Controllers via SSH, downloads backups, and converts all configuration data to JSON format for easy analysis and documentation.

## Features

- **Automated Backup Downloads**: Connects to UniFi controllers via SSH and downloads the latest backup files
- **Backup Decryption**: Automatically decrypts `.unf` backup files using UniFi's standard encryption
- **Configuration Conversion**: Converts BSON, configuration files, and properties to JSON format
- **Git Version Control**: Maintains a Git repository of backup changes for tracking configuration evolution
- **Scheduled Operations**: Configurable cron-based scheduling (daily/weekly/custom)
- **Backup Retention**: Automatic cleanup of old backups based on retention policies
- **Multi-Architecture**: Supports AMD64, ARM64, and ARM v7 platforms
- **Timezone Support**: Configurable timezone for accurate scheduling
- **Comprehensive Logging**: Detailed logging for monitoring and troubleshooting

## Quick Start

### Using Docker Compose (Recommended)

1. Copy the example compose file:
```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/loryanstrant/unifi-documenter/main/docker-compose.example.yml
```

2. Edit the environment variables:
```yaml
environment:
  UNIFI_HOST: "192.168.1.1"              # Your UniFi controller IP
  UNIFI_SSH_USER: "root"                 # SSH username
  UNIFI_SSH_PASSWORD: "your-password"    # SSH password
  BACKUP_SCHEDULE: "0 2 * * *"           # Daily at 2 AM
  TZ: "America/New_York"                 # Your timezone
```

3. Start the container:
```bash
docker-compose up -d
```

### Using Docker CLI

```bash
docker run -d \
  --name unifi-documenter \
  --restart unless-stopped \
  -e UNIFI_HOST=192.168.1.1 \
  -e UNIFI_SSH_USER=root \
  -e UNIFI_SSH_PASSWORD=your-password \
  -e BACKUP_SCHEDULE="0 2 * * *" \
  -e TZ=America/New_York \
  -v ./unifi-backups:/backups \
  -v ./logs:/app/logs \
  ghcr.io/loryanstrant/unifi-documenter:latest
```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `UNIFI_HOST` | IP address or hostname of UniFi controller | `192.168.1.1` |
| `UNIFI_SSH_USER` | SSH username (usually 'root' for UDM) | `root` |

### Authentication (Choose One)

| Variable | Description | Example |
|----------|-------------|---------|
| `UNIFI_SSH_PASSWORD` | SSH password | `your-secure-password` |
| `UNIFI_SSH_KEY` | SSH private key content | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UNIFI_SSH_PORT` | `22` | SSH port number |
| `UNIFI_BACKUP_PASSWORD` | `""` | Backup encryption password (if set on controller) |
| `BACKUP_SCHEDULE` | `"0 2 * * *"` | Cron schedule for backups |
| `BACKUP_RETENTION_DAYS` | `30` | Days to keep archived backups |
| `TZ` | `UTC` | Timezone for scheduling |
| `RUN_ONCE` | `false` | Set to `true` for one-time backup and exit |

### Cron Schedule Examples

| Schedule | Description |
|----------|-------------|
| `"0 2 * * *"` | Daily at 2:00 AM |
| `"0 3 * * 0"` | Weekly on Sunday at 3:00 AM |
| `"0 1 1 * *"` | Monthly on the 1st at 1:00 AM |
| `"*/6 * * * *"` | Every 6 hours |

## Directory Structure

The container creates the following structure in `/backups`:

```
/backups/
├── README.md                    # Repository documentation
├── latest/                      # Latest backup (JSON format)
│   ├── metadata.json           # Backup metadata
│   ├── system.properties.json  # System configuration
│   ├── sites/                  # Site configurations
│   │   └── default/
│   │       ├── config.json     # Site config
│   │       ├── users.bson.json # User data
│   │       └── ...
│   └── .git/                   # Git repository
└── archives/                   # Archived backups
    ├── backup_20231201_020000.tar.gz
    └── backup_20231202_020000.tar.gz
```

## Data Conversion

The tool converts various UniFi configuration formats to JSON:

- **BSON files** → JSON (MongoDB collections like users, devices, settings)
- **`.conf` files** → JSON (Java properties format)
- **`.properties` files** → JSON (Key-value configurations)
- **Existing JSON files** → Copied as-is

### Example Converted Data

```json
{
  "backup_date": "2023-12-01T02:00:00",
  "source_host": "192.168.1.1",
  "files_converted": 47,
  "site_config": {
    "name": "default",
    "description": "Default Site",
    "devices": [...]
  }
}
```

## SSH Key Authentication

For enhanced security, use SSH key authentication:

1. Generate SSH key pair:
```bash
ssh-keygen -t rsa -b 4096 -f ./unifi-ssh-key
```

2. Copy public key to UniFi controller:
```bash
ssh-copy-id -i ./unifi-ssh-key.pub root@192.168.1.1
```

3. Configure Docker with private key:
```yaml
environment:
  UNIFI_SSH_KEY: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
    # ... rest of private key content
    -----END OPENSSH PRIVATE KEY-----
```

## Monitoring and Troubleshooting

### View Logs

```bash
# View real-time logs
docker logs -f unifi-documenter

# View backup logs
docker exec unifi-documenter tail -f /app/logs/backup.log

# View cron logs
docker exec unifi-documenter tail -f /app/logs/cron.log
```

### Manual Backup

Run a one-time backup:

```bash
# Using existing container
docker exec unifi-documenter python3 /app/backup.py

# Using temporary container
docker run --rm \
  -e UNIFI_HOST=192.168.1.1 \
  -e UNIFI_SSH_USER=root \
  -e UNIFI_SSH_PASSWORD=your-password \
  -e RUN_ONCE=true \
  -v ./backup-test:/backups \
  ghcr.io/loryanstrant/unifi-documenter:latest
```

### Health Check

The container includes a health check endpoint:

```bash
docker exec unifi-documenter python3 -c "import sys; sys.exit(0)"
```

## Supported UniFi Devices

- UniFi Dream Machine (UDM)
- UniFi Dream Machine Pro (UDM-Pro)
- UniFi Dream Machine SE (UDM-SE)
- UniFi Dream Router (UDR)
- UniFi Cloud Key Gen2/Gen2+
- Self-hosted UniFi Network Controller

## Security Considerations

- **SSH Access**: Ensure SSH is enabled and accessible from the container network
- **Credentials**: Use SSH keys instead of passwords when possible
- **Network Security**: Run on isolated networks when possible
- **Backup Security**: Backup files may contain sensitive configuration data
- **File Permissions**: Container runs as non-root user (UID 1000)

## Building from Source

```bash
# Clone repository
git clone https://github.com/loryanstrant/unifi-documenter.git
cd unifi-documenter

# Build Docker image
docker build -t unifi-documenter .

# Run tests
docker run --rm -v $(pwd):/app unifi-documenter python3 test_backup.py
```

## Development

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
python3 test_backup.py

# Run with coverage
coverage run test_backup.py
coverage report
```

### Local Development

```bash
# Set environment variables
export UNIFI_HOST=192.168.1.1
export UNIFI_SSH_USER=root
export UNIFI_SSH_PASSWORD=your-password

# Run backup script
python3 backup.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run tests: `python3 test_backup.py`
5. Commit changes: `git commit -am 'Add new feature'`
6. Push to branch: `git push origin feature/new-feature`
7. Create Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0
- Initial release
- UniFi backup download and decryption
- Configuration conversion to JSON
- Git version control integration
- Scheduled backup operations
- Multi-architecture Docker support
- Comprehensive documentation and testing

## Support

- **Issues**: [GitHub Issues](https://github.com/loryanstrant/unifi-documenter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/loryanstrant/unifi-documenter/discussions)
- **Documentation**: [GitHub Wiki](https://github.com/loryanstrant/unifi-documenter/wiki)

## Acknowledgments

- UniFi community for reverse engineering backup formats
- Ubiquiti for creating excellent networking hardware
- Contributors and testers who helped improve this tool