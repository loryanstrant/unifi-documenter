# Container Resource Configuration

This document explains the resource limits configured for the UniFi Documenter container and how to adjust them for your environment.

## Default Resource Limits

The container is configured with the following resource constraints to prevent system overload:

### CPU Limits
- **Maximum**: 2.0 cores
- **Reserved**: 0.5 cores
- This ensures the container cannot monopolize all CPU resources

### Memory Limits
- **Maximum**: 2GB RAM
- **Reserved**: 512MB RAM
- Prevents out-of-memory situations from affecting the host system

### Process Limits
- **Maximum PIDs**: 200 processes
- Prevents fork bombs or runaway process creation

### Additional Protections
- **Swap**: Disabled (`mem_swappiness: 0`) to prevent disk thrashing
- **OOM Killer**: Enabled as a safety mechanism to prevent system-wide freezes

## Adjusting Resource Limits

### For Low-Resource Systems

If your system has limited resources (e.g., 4GB RAM total, 2 CPU cores):

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'          # Use max 1 CPU core
      memory: 1G           # Use max 1GB RAM
    reservations:
      cpus: '0.25'         # Reserve 0.25 cores
      memory: 256M         # Reserve 256MB RAM
pids_limit: 100            # Reduce process limit
```

### For High-Resource Systems

If your system has abundant resources (e.g., 16GB+ RAM, 8+ CPU cores):

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'          # Use max 4 CPU cores
      memory: 4G           # Use max 4GB RAM
    reservations:
      cpus: '1.0'          # Reserve 1 core
      memory: 1G           # Reserve 1GB RAM
pids_limit: 500            # Higher process limit
```

### For Portainer Stack Configuration

When using Portainer, add the following to your stack configuration under the `unifi-documenter` service:

```yaml
services:
  unifi-documenter:
    # ... existing configuration ...
    
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    
    mem_swappiness: 0
    oom_kill_disable: false
    pids_limit: 200
```

## Monitoring Resource Usage

### View Container Resource Usage

```bash
# Real-time monitoring
docker stats UnifiDocumenter

# One-time check
docker stats UnifiDocumenter --no-stream
```

### Check if Limits are Being Hit

```bash
# Check for OOM kills
docker inspect UnifiDocumenter | grep -i oom

# View container logs for resource-related issues
docker logs UnifiDocumenter | grep -i "memory\|timeout\|killed"
```

## Timeout Protection

The application now includes built-in timeout protection:

- **Decryption Timeout**: 5 minutes (300 seconds)
- **SSH Operations**: 10 seconds

These timeouts prevent operations from hanging indefinitely. If you need to adjust them, modify the `timeout_seconds` parameter in the code:

```python
# In src/backup_processor.py
if not self.decrypt_unf_file(local_backup, decrypted_zip, timeout_seconds=600):  # 10 minutes
```

## Troubleshooting

### Container Keeps Getting Killed

If the container is repeatedly killed by the OOM killer:

1. Increase the memory limit
2. Check for memory leaks in logs
3. Verify backup file sizes aren't excessively large

### Container is Too Slow

If processing is taking too long:

1. Increase CPU allocation
2. Check if disk I/O is the bottleneck
3. Review logs for timeout warnings

### System Still Becomes Unresponsive

If the host system still becomes unresponsive despite limits:

1. Reduce the CPU limit further (e.g., to `1.0` or `0.5`)
2. Reduce memory limit to free up more system resources
3. Consider running the container on a dedicated system
4. Check for other resource-intensive containers

## Resource Calculation Guidelines

### Minimum Requirements
- **CPU**: 0.5 cores
- **RAM**: 512MB
- **Disk**: 2GB free space for temporary files

### Recommended Resources
- **CPU**: 2.0 cores
- **RAM**: 2GB
- **Disk**: 5GB free space

### Optimal Resources (for large backups)
- **CPU**: 4.0 cores
- **RAM**: 4GB
- **Disk**: 10GB free space

## Best Practices

1. **Start Conservative**: Begin with lower limits and increase if needed
2. **Monitor First Week**: Watch resource usage during the first week of operation
3. **Adjust Based on Backup Size**: Larger UniFi networks generate larger backups
4. **Schedule Off-Peak**: Run during low-usage periods (default: 2 AM)
5. **Regular Cleanup**: The container automatically manages old files, but verify disk space periodically

## Emergency Recovery

If the container causes system issues:

```bash
# Immediately stop the container
docker stop UnifiDocumenter

# Check system resources
free -h
top

# Remove problematic container
docker rm UnifiDocumenter

# Restart with stricter limits
# (modify docker-compose.yml with lower limits first)
docker-compose up -d
```
