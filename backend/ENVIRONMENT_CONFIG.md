# Environment Configuration Guide

This document outlines the environment variables used to configure the RichardOps monitoring backend.

## Required Environment Variables

### `INGEST_SECRET`
- **Description:** Shared secret for HMAC signature verification
- **Required:** Yes
- **Example:** `INGEST_SECRET=your-super-secret-key-here`
- **Security:** Keep this secret secure and rotate regularly

## Optional Environment Variables

### `HMAC_TIMESTAMP_WINDOW`
- **Description:** Maximum allowed time difference (in seconds) between client and server timestamps
- **Default:** `300` (5 minutes)
- **Recommended Values:**
  - Development: `300` (5 minutes)
  - Production: `300` (5 minutes) - allows for reasonable clock drift
  - Strict Security: `120` (2 minutes) - for environments with synchronized clocks
- **Example:** `HMAC_TIMESTAMP_WINDOW=300`

### `ENVIRONMENT`
- **Description:** Environment identifier for the application
- **Default:** `development`
- **Values:** `development`, `staging`, `production`
- **Example:** `ENVIRONMENT=production`
- **Effect:** 
  - In production: Disables `/docs`, `/redoc`, and `/openapi.json` endpoints
  - In development: Enables interactive API documentation

### Database Configuration

### `DATABASE_URL`
- **Description:** PostgreSQL database connection string
- **Required:** Yes (if using external database)
- **Example:** `DATABASE_URL=postgresql://user:password@localhost:5432/monitoring`

## Docker Environment File

Create a `.env` file for Docker deployments:

```bash
# Security
INGEST_SECRET=your-super-secret-key-here
HMAC_TIMESTAMP_WINDOW=300

# Environment
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://postgres:password@db:5432/monitoring

# Optional: Logging
LOG_LEVEL=INFO
```

## Production Recommendations

### Security Settings
```bash
# Use a strong, randomly generated secret
INGEST_SECRET=$(openssl rand -hex 32)

# Use reasonable timestamp window for production
HMAC_TIMESTAMP_WINDOW=300

# Set production environment
ENVIRONMENT=production
```

### Clock Synchronization
- Ensure both client and server systems have synchronized clocks (NTP)
- Monitor clock drift warnings in logs
- Consider using a shorter timestamp window (120s) if clocks are well-synchronized

### Monitoring
- Monitor logs for "Clock drift detected" warnings
- Monitor logs for "Request timestamp is stale" errors
- Set up alerts for authentication failures

## Troubleshooting

### "Request timestamp is stale" Errors

**Symptoms:**
```
Request timestamp is stale: time_diff=350s, window=300s
```

**Solutions:**
1. **Check clock synchronization:**
   ```bash
   # On client system
   ntpdate -q pool.ntp.org
   
   # On server system  
   ntpdate -q pool.ntp.org
   ```

2. **Increase timestamp window temporarily:**
   ```bash
   HMAC_TIMESTAMP_WINDOW=600  # 10 minutes
   ```

3. **Check network latency:**
   - High network latency can contribute to timestamp issues
   - Consider the total round-trip time in your timestamp window

### Clock Drift Warnings

**Symptoms:**
```
Clock drift detected: 75s difference between client and server
```

**Solutions:**
1. **Synchronize clocks using NTP:**
   ```bash
   # Ubuntu/Debian
   sudo apt install ntp
   sudo systemctl enable ntp
   sudo systemctl start ntp
   
   # CentOS/RHEL
   sudo yum install ntp
   sudo systemctl enable ntpd
   sudo systemctl start ntpd
   ```

2. **Check timezone settings:**
   - Ensure both systems use UTC or the same timezone
   - The Go client uses UTC timestamps

3. **Monitor regularly:**
   - Set up monitoring for clock drift warnings
   - Consider automated clock synchronization

## Example Docker Compose

```yaml
version: '3.8'
services:
  monitoring-backend:
    build: .
    environment:
      - INGEST_SECRET=${INGEST_SECRET}
      - HMAC_TIMESTAMP_WINDOW=300
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/monitoring
    ports:
      - "8000:8000"
    depends_on:
      - db
      
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=monitoring
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Security Best Practices

1. **Rotate secrets regularly:** Change `INGEST_SECRET` periodically
2. **Use strong secrets:** Generate with `openssl rand -hex 32`
3. **Monitor authentication:** Set up alerts for failed HMAC verifications
4. **Secure environment files:** Protect `.env` files with appropriate permissions
5. **Use HTTPS:** Always use HTTPS in production environments
6. **Network security:** Restrict access to the monitoring backend to authorized clients only

## Performance Considerations

- **Timestamp Window:** Shorter windows provide better security but require better clock synchronization
- **Clock Drift Monitoring:** Regular monitoring helps prevent authentication issues
- **Database Performance:** Ensure database connections are properly configured for your load
- **Log Rotation:** Configure log rotation to prevent disk space issues