# Production Deployment Guide

## Overview
This guide covers deploying the monitoring backend to production with proper security, scalability, and reliability configurations.

## Prerequisites
- Docker and Docker Compose installed
- PostgreSQL database (can use included Docker setup)
- SSL/TLS certificates (for HTTPS)
- Reverse proxy (nginx/traefik recommended)

## Quick Start

### 1. Environment Configuration
```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your production values
nano .env
```

**Critical Environment Variables:**
- `INGEST_SECRET`: Strong shared secret for HMAC authentication
- `DATABASE_URL`: Production PostgreSQL connection string
- `UVICORN_WORKERS`: Number of worker processes (recommended: CPU cores)

### 2. Production Deployment
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check service health
docker-compose -f docker-compose.prod.yml ps
```

### 3. Database Migration
```bash
# Run database migrations
docker exec -it monitoring-backend-prod alembic upgrade head
```

## Security Checklist

### ✅ Authentication & Authorization
- [x] HMAC signature verification implemented
- [x] Timestamp validation (120-second window)
- [x] Strong secret key required (`INGEST_SECRET`)

### ✅ Infrastructure Security
- [x] Non-root user in Docker container
- [x] TrustedHost middleware configured
- [x] CORS properly configured
- [x] Health checks implemented

### ⚠️ Production Security Requirements
- [ ] Configure specific allowed hosts in `TrustedHostMiddleware`
- [ ] Configure specific CORS origins (remove `*`)
- [ ] Use HTTPS with SSL/TLS certificates
- [ ] Implement rate limiting
- [ ] Set up log rotation
- [ ] Configure firewall rules

## Production Configuration

### Environment Variables
```bash
# Security
INGEST_SECRET=your-very-strong-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/monitoring

# Application
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
UVICORN_WORKERS=4
UVICORN_RELOAD=false
LOG_LEVEL=info

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@yourcompany.com
SMTP_PASSWORD=your-app-password
```

### Reverse Proxy (Nginx Example)
```nginx
server {
    listen 443 ssl http2;
    server_name monitoring.yourcompany.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /healthz {
        proxy_pass http://localhost:8000/healthz;
        access_log off;
    }
}
```

## Monitoring & Observability

### Health Checks
- **Endpoint**: `GET /healthz`
- **Docker**: Built-in health check configured
- **Kubernetes**: Ready for liveness/readiness probes

### Logging
- **Application logs**: `/app/logs/ingest.log`
- **Alert logs**: `/app/logs/alerts.log` (structured JSON)
- **Access logs**: Uvicorn access logging enabled

### Metrics
- Database connection pooling metrics
- Request/response metrics via FastAPI
- Custom business metrics via `/metrics/recent` endpoint

## Scaling Considerations

### Horizontal Scaling
- Stateless application design
- Database connection pooling
- Multiple worker processes supported

### Database Optimization
- Connection pooling configured
- Indexes on frequently queried columns
- Connection recycling (300 seconds)

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

## Backup & Recovery

### Database Backups
```bash
# Create backup
docker exec monitoring-postgres-prod pg_dump -U monitoring_user monitoring > backup.sql

# Restore backup
docker exec -i monitoring-postgres-prod psql -U monitoring_user monitoring < backup.sql
```

### Log Rotation
```bash
# Add to crontab for log rotation
0 0 * * * docker exec monitoring-backend-prod logrotate /etc/logrotate.conf
```

## Troubleshooting

### Common Issues
1. **Database Connection Failed**
   - Check `DATABASE_URL` format
   - Verify PostgreSQL is running
   - Check network connectivity

2. **HMAC Signature Invalid**
   - Verify `INGEST_SECRET` matches client
   - Check timestamp synchronization
   - Validate request format

3. **High Memory Usage**
   - Reduce `UVICORN_WORKERS`
   - Check for memory leaks in logs
   - Monitor database connection pool

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=debug
docker-compose -f docker-compose.prod.yml restart monitoring-backend
```

## Security Hardening

### Additional Recommendations
1. **Network Security**
   - Use private networks
   - Implement VPN access
   - Configure firewall rules

2. **Container Security**
   - Regular image updates
   - Vulnerability scanning
   - Minimal base images

3. **Secrets Management**
   - Use Docker secrets or external secret managers
   - Rotate secrets regularly
   - Audit secret access

4. **Monitoring**
   - Set up alerting for failed health checks
   - Monitor resource usage
   - Track authentication failures

## Performance Tuning

### Database
- Tune PostgreSQL configuration
- Monitor query performance
- Implement read replicas if needed

### Application
- Adjust worker count based on CPU cores
- Monitor memory usage per worker
- Implement caching if needed

### Network
- Use HTTP/2
- Enable gzip compression
- Implement CDN for static assets

## Compliance & Auditing

### Logging Requirements
- All authentication attempts logged
- Database operations audited
- Error conditions tracked

### Data Retention
- Configure log retention policies
- Implement data archiving
- Regular cleanup procedures

---

## Support
For issues or questions, check the application logs and health endpoints first. The monitoring backend provides comprehensive error reporting and health status information.