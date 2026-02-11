# Deployment Guide

## Production Checklist

### Backend

- [ ] Set `DEBUG=false` in production
- [ ] Use strong `JWT_SECRET_KEY`
- [ ] Configure proper CORS origins
- [ ] Set up SSL/HTTPS
- [ ] Enable rate limiting
- [ ] Configure logging to external service
- [ ] Set up database backups
- [ ] Configure health checks
- [ ] Set up monitoring (e.g., Sentry)
- [ ] Review and test RLS policies

### Frontend

- [ ] Set production API URL
- [ ] Configure Supabase production keys
- [ ] Enable image optimization
- [ ] Set up CDN for static assets
- [ ] Configure proper CSP headers
- [ ] Enable compression
- [ ] Set up error tracking
- [ ] Test mobile responsiveness

## Deployment Options

### Option 1: Docker + Cloud Provider

**Backend (AWS ECS, Google Cloud Run, Azure Container Instances)**

```bash
# Build image
docker build -t educore-backend ./backend

# Tag for registry
docker tag educore-backend:latest your-registry/educore-backend:latest

# Push to registry
docker push your-registry/educore-backend:latest

# Deploy to cloud provider
# Follow provider-specific instructions
```

**Frontend (Vercel - Recommended)**

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod
```

### Option 2: Traditional VPS

**Backend Setup**

```bash
# Install dependencies
sudo apt update
sudo apt install python3.11 python3-pip nginx supervisor

# Clone repository
git clone your-repo
cd EduSMS/backend

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure supervisor
sudo nano /etc/supervisor/conf.d/educore.conf
```

Supervisor config:
```ini
[program:educore]
directory=/path/to/EduSMS/backend
command=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/educore.err.log
stdout_logfile=/var/log/educore.out.log
```

**Nginx Configuration**

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**SSL with Let's Encrypt**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

### Option 3: Kubernetes

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: educore-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: educore-backend
  template:
    metadata:
      labels:
        app: educore-backend
    spec:
      containers:
      - name: backend
        image: your-registry/educore-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "false"
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: educore-secrets
              key: supabase-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Environment Variables

### Production Backend

```env
DEBUG=false
APP_NAME=EduCore API
APP_VERSION=1.0.0

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_production_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_production_service_key

JWT_SECRET_KEY=your_very_strong_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

CORS_ORIGINS=["https://yourdomain.com"]

# Optional: Sentry for error tracking
SENTRY_DSN=your_sentry_dsn
```

### Production Frontend

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_production_anon_key
```

## Monitoring & Logging

### Sentry Integration (Backend)

```python
# Add to requirements.txt
sentry-sdk[fastapi]>=1.40.0

# Add to app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if not settings.DEBUG and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
    )
```

### Log Aggregation

Use services like:
- AWS CloudWatch
- Google Cloud Logging
- Datadog
- Loggly

## Database Backups

### Supabase Backups

Supabase provides automatic daily backups. For additional safety:

```bash
# Manual backup
pg_dump -h db.your-project.supabase.co -U postgres -d postgres > backup.sql

# Restore
psql -h db.your-project.supabase.co -U postgres -d postgres < backup.sql
```

## Performance Optimization

### Backend

1. Enable response caching
2. Use connection pooling
3. Add database indexes
4. Implement pagination
5. Use async operations

### Frontend

1. Enable Next.js image optimization
2. Use dynamic imports for large components
3. Implement route prefetching
4. Enable compression
5. Use CDN for static assets

## Security Hardening

1. Keep dependencies updated
2. Use security headers
3. Implement rate limiting
4. Enable HTTPS only
5. Regular security audits
6. Monitor for vulnerabilities
7. Implement IP whitelisting for admin routes
8. Use secrets management service

## Scaling Considerations

### Horizontal Scaling

- Use load balancer (AWS ALB, Nginx)
- Deploy multiple backend instances
- Use Redis for session storage
- Implement caching layer

### Database Scaling

- Enable read replicas
- Implement connection pooling
- Use database indexes
- Consider sharding for large datasets

## Rollback Strategy

```bash
# Tag releases
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Rollback if needed
git checkout v1.0.0
# Redeploy
```

## Health Checks

Backend health endpoint: `GET /health`

Expected response:
```json
{
  "status": "healthy",
  "app": "EduCore API",
  "version": "1.0.0"
}
```

## Support

For deployment issues, check:
1. Application logs
2. Server logs
3. Database connection
4. Environment variables
5. Network/firewall rules
