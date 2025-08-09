# Examples and Use Cases

This directory contains practical examples for deploying and using the Unifi Backup Container in various scenarios.

## Basic Examples

### Single Controller - Daily Backup
```yaml
# docker-compose.yml
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

### Multiple Controllers
```yaml
# docker-compose.yml
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

## Advanced Examples

### Custom Cron Schedule
```yaml
# Every 6 hours
environment:
  BACKUP_SCHEDULE: "cron:0 */6 * * *"
  
# Weekdays only at 2 AM
environment:
  BACKUP_SCHEDULE: "cron:0 2 * * 1-5"
  
# First day of month
environment:
  BACKUP_SCHEDULE: "cron:0 2 1 * *"
```

### Production Setup with Monitoring
```yaml
version: '3.8'
services:
  unifi-backup:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    container_name: unifi-backup
    restart: unless-stopped
    environment:
      UNIFI_HOST: "udm.example.com"
      UNIFI_USERNAME: "backup-user"
      UNIFI_PASSWORD_FILE: "/run/secrets/unifi_password"
      BACKUP_SCHEDULE: "daily"
      BACKUP_TIME: "01:30"
      BACKUP_RETENTION_DAYS: "90"
      TZ: "UTC"
      LOG_LEVEL: "INFO"
    volumes:
      - backup-data:/app/backups
      - backup-logs:/app/logs
    ports:
      - "8080:8080"
    secrets:
      - unifi_password
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Log aggregation
  fluentd:
    image: fluentd:latest
    volumes:
      - backup-logs:/fluentd/log

secrets:
  unifi_password:
    file: ./secrets/unifi_password.txt

volumes:
  backup-data:
  backup-logs:
```

### Docker Swarm Deployment
```yaml
version: '3.8'
services:
  unifi-backup:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    environment:
      UNIFI_HOST: "udm.internal.example.com"
      UNIFI_USERNAME: "backup"
      UNIFI_PASSWORD: "secure-password"
      BACKUP_SCHEDULE: "daily"
      BACKUP_TIME: "02:00"
    volumes:
      - type: volume
        source: backup-storage
        target: /app/backups
    ports:
      - "8080:8080"
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == worker
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    networks:
      - backup-network

volumes:
  backup-storage:
    driver: local

networks:
  backup-network:
    driver: overlay
```

## Kubernetes Examples

### Basic Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unifi-backup
spec:
  replicas: 1
  selector:
    matchLabels:
      app: unifi-backup
  template:
    metadata:
      labels:
        app: unifi-backup
    spec:
      containers:
      - name: unifi-backup
        image: ghcr.io/loryanstrant/unifi-documenter:latest
        env:
        - name: UNIFI_HOST
          value: "192.168.1.1"
        - name: UNIFI_USERNAME
          valueFrom:
            secretKeyRef:
              name: unifi-credentials
              key: username
        - name: UNIFI_PASSWORD
          valueFrom:
            secretKeyRef:
              name: unifi-credentials
              key: password
        - name: BACKUP_SCHEDULE
          value: "daily"
        - name: BACKUP_TIME
          value: "02:00"
        - name: TZ
          value: "UTC"
        volumeMounts:
        - name: backup-storage
          mountPath: /app/backups
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: backup-storage
        persistentVolumeClaim:
          claimName: backup-pvc
---
apiVersion: v1
kind: Secret
metadata:
  name: unifi-credentials
type: Opaque
stringData:
  username: "root"
  password: "your-password"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: backup-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: unifi-backup-service
spec:
  selector:
    app: unifi-backup
  ports:
    - port: 8080
      targetPort: 8080
  type: ClusterIP
```

## CLI Usage Examples

### One-time Backup
```bash
# Run immediate backup
docker run --rm \
  -e UNIFI_HOST=192.168.1.1 \
  -e UNIFI_USERNAME=root \
  -e UNIFI_PASSWORD=password \
  -v $(pwd)/backups:/app/backups \
  ghcr.io/loryanstrant/unifi-documenter:latest once
```

### Test Connection
```bash
# Test SSH connectivity
docker run --rm \
  -e UNIFI_HOST=192.168.1.1 \
  -e UNIFI_USERNAME=root \
  -e UNIFI_PASSWORD=password \
  ghcr.io/loryanstrant/unifi-documenter:latest test
```

### Debug Mode
```bash
# Run with debug logging
docker run --rm \
  -e UNIFI_HOST=192.168.1.1 \
  -e UNIFI_USERNAME=root \
  -e UNIFI_PASSWORD=password \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/backups:/app/backups \
  ghcr.io/loryanstrant/unifi-documenter:latest once
```

## Integration Examples

### Backup to Cloud Storage
```bash
#!/bin/bash
# backup-to-cloud.sh

# Run backup
docker run --rm \
  -e UNIFI_HOST=192.168.1.1 \
  -e UNIFI_USERNAME=root \
  -e UNIFI_PASSWORD=password \
  -v $(pwd)/backups:/app/backups \
  ghcr.io/loryanstrant/unifi-documenter:latest once

# Sync to cloud (example with rclone)
rclone sync ./backups/ remote:unifi-backups/
```

### Notification Integration
```yaml
# docker-compose.yml with notifications
version: '3.8'
services:
  unifi-backup:
    image: ghcr.io/loryanstrant/unifi-documenter:latest
    environment:
      UNIFI_HOST: "192.168.1.1"
      UNIFI_USERNAME: "root"
      UNIFI_PASSWORD: "password"
    volumes:
      - ./backups:/app/backups
      - ./scripts:/scripts
    command: >
      sh -c "
        /app/entrypoint.sh &
        while true; do
          if /scripts/check-backup-status.sh; then
            /scripts/send-notification.sh 'Backup successful'
          else
            /scripts/send-notification.sh 'Backup failed'
          fi
          sleep 3600
        done
      "
```

## Troubleshooting Examples

### Debug Container Issues
```bash
# Check container logs
docker logs unifi-backup

# Execute commands inside container
docker exec -it unifi-backup /bin/bash

# Check health status
curl http://localhost:8080/health | jq '.'

# Validate configuration
docker exec unifi-backup python3 /app/validate.py
```

### Network Troubleshooting
```bash
# Test network connectivity from container
docker exec unifi-backup ping 192.168.1.1
docker exec unifi-backup nc -zv 192.168.1.1 22
docker exec unifi-backup ssh -o ConnectTimeout=5 root@192.168.1.1 'echo "Connection OK"'
```

## Backup Analysis Examples

### Parse Backup JSON
```python
#!/usr/bin/env python3
import json
import sys

# Load complete backup
with open('backups/backup_20231215_143022/json_20231215_143022/complete_backup.json', 'r') as f:
    backup_data = json.load(f)

# Analyze devices
devices = backup_data.get('devices', {})
print(f"Found {len(devices)} device categories")

for category, device_list in devices.items():
    if isinstance(device_list, list):
        print(f"  {category}: {len(device_list)} devices")
        for device in device_list[:3]:  # Show first 3
            name = device.get('name', 'Unknown')
            model = device.get('model', 'Unknown')
            print(f"    - {name} ({model})")
```

### Backup Comparison
```bash
#!/bin/bash
# compare-backups.sh

BACKUP1="backups/backup_20231214_020000/json_20231214_020000/complete_backup.json"
BACKUP2="backups/backup_20231215_020000/json_20231215_020000/complete_backup.json"

# Compare device counts
echo "Device comparison:"
jq '.devices | keys[] as $k | "\($k): \(.[$k] | length)"' "$BACKUP1" > /tmp/devices1.txt
jq '.devices | keys[] as $k | "\($k): \(.[$k] | length)"' "$BACKUP2" > /tmp/devices2.txt
diff /tmp/devices1.txt /tmp/devices2.txt

# Compare network settings
echo "Network comparison:"
diff <(jq '.networks' "$BACKUP1") <(jq '.networks' "$BACKUP2")
```

For more examples and use cases, see the main [README.md](../README.md) file.