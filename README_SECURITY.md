# Security Considerations

## Web Interface Security

The UniFi Documenter includes a web interface for monitoring progress and viewing results. Please be aware of the following security considerations:

### Network Binding
- The web server binds to `0.0.0.0` by default to allow access from any network interface
- **Recommendation**: Use Docker port mapping to control access (e.g., `-p 127.0.0.1:8080:8080` for localhost only)
- For production deployments, consider placing behind a reverse proxy with authentication (nginx, Caddy, Traefik)

### Authentication
- The web interface currently has **no authentication**
- This is intentional for simple local deployments and container environments
- **For production**: Implement one of the following:
  - Place behind authenticated reverse proxy
  - Use network-level access controls (firewall, VPN)
  - Run in isolated environment (localhost only, private network)

### Input Validation
- Path traversal protection is implemented for file endpoints
- HTML output is sanitized to prevent XSS attacks
- File uploads should only be performed in trusted environments

### Deployment Recommendations

**For Development/Testing:**
```bash
docker run -p 127.0.0.1:8080:8080 unifi-documenter
```

**For Production:**
```yaml
# docker-compose.yml with reverse proxy
services:
  unifi-documenter:
    image: unifi-documenter
    networks:
      - internal
    # No exposed ports - proxy only
  
  nginx:
    image: nginx
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    networks:
      - internal
```

## Reporting Security Issues

If you discover a security vulnerability, please email security@yourdomain.com instead of using the issue tracker.
