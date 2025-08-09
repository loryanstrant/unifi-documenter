# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by:

1. **DO NOT** create a public GitHub issue
2. Send an email to the repository maintainer with details
3. Include steps to reproduce the vulnerability
4. Provide any relevant technical details

## Security Features

This container implements several security best practices:

### Container Security
- Runs as non-root user (UID 1000)
- Minimal base image with only required dependencies
- Multi-stage build to reduce attack surface
- No unnecessary ports exposed
- Proper signal handling for graceful shutdown

### Credential Security
- Credentials passed via environment variables only
- No credential persistence in logs or files
- Secure SSH connection handling
- Automatic connection cleanup

### Network Security
- Configurable connection timeouts
- No persistent network connections
- SSH-only communication with controllers
- Optional network isolation support

### Data Security
- Local-only backup storage
- Configurable backup retention
- No external data transmission
- Backup file validation

## Recommendations

### Production Deployment
1. Use SSH key authentication instead of passwords when possible
2. Run container in isolated network/VLAN
3. Encrypt backup storage volumes
4. Regularly update container images
5. Monitor container logs for security events
6. Implement backup storage access controls

### Network Configuration
1. Limit SSH access to backup container only
2. Use firewall rules to restrict container network access
3. Consider VPN or secure tunneling for remote controllers
4. Monitor SSH connection attempts

### Backup Security
1. Encrypt backup storage at rest
2. Implement backup integrity checking
3. Secure backup transmission if using remote storage
4. Regular backup restore testing
5. Access logging for backup files

## Known Security Considerations

1. **SSH Password Authentication**: Currently uses password authentication. Consider implementing SSH key support for enhanced security.

2. **Backup Decryption**: Handles encrypted .unf files with known decryption methods. Some backup files may contain sensitive network configuration data.

3. **Container Privileges**: Requires network access to reach Unifi controllers. Ensure appropriate network security controls.

4. **Log Data**: Container logs may contain connection information. Ensure log security in your environment.

## Updates and Patches

- Monitor GitHub releases for security updates
- Subscribe to security advisories
- Test updates in non-production environment first
- Maintain backup of working container versions

## Contact

For security-related questions or to report vulnerabilities, please contact the repository maintainer through GitHub.