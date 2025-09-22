# Deployment Guide

Comprehensive deployment instructions for the AKCN Project Management System backend.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Preparation](#environment-preparation)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration](#configuration)
7. [SSL/TLS Setup](#ssltls-setup)
8. [Monitoring Setup](#monitoring-setup)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Disk**: 20GB minimum (SSD recommended)
- **Python**: 3.8+ (3.10 recommended)
- **PostgreSQL**: 14+
- **Redis**: 5.0+ (optional)

### Network Requirements
- Port 8000 for API service
- Port 5432 for PostgreSQL
- Port 6379 for Redis (if used)
- Port 80/443 for web traffic (production)

## Environment Preparation

### 1. Update System
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx supervisor

# CentOS/RHEL
sudo yum update -y
sudo yum install -y python3 python3-pip git nginx supervisor

# Install PostgreSQL
# Ubuntu/Debian
sudo apt install -y postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install -y postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
```

### 2. Create Application User
```bash
# Create dedicated user for application
sudo adduser --system --group akcn
sudo mkdir -p /opt/akcn
sudo chown -R akcn:akcn /opt/akcn
```

### 3. Setup PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE USER akcn_user WITH PASSWORD 'strong_password_here';
CREATE DATABASE akcn_prod_db WITH OWNER = akcn_user;
GRANT ALL PRIVILEGES ON DATABASE akcn_prod_db TO akcn_user;
\q

# Configure PostgreSQL for network access (if needed)
# Edit /etc/postgresql/14/main/postgresql.conf
listen_addresses = 'localhost'  # or '*' for all interfaces

# Edit /etc/postgresql/14/main/pg_hba.conf
host    akcn_prod_db    akcn_user    127.0.0.1/32    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Docker Deployment

### 1. Create Dockerfile
```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 akcn && chown -R akcn:akcn /app
USER akcn

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Create docker-compose.yml
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    restart: always
    environment:
      POSTGRES_USER: akcn_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: akcn_prod_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - akcn_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U akcn_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - akcn_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    restart: always
    environment:
      DATABASE_URL: postgresql+asyncpg://akcn_user:${DB_PASSWORD}@db:5432/akcn_prod_db
      REDIS_URL: redis://redis:6379
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENVIRONMENT: production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    networks:
      - akcn_network
    volumes:
      - ./logs:/app/logs

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - akcn_network

volumes:
  postgres_data:
  redis_data:

networks:
  akcn_network:
    driver: bridge
```

### 3. Deploy with Docker
```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f app

# Scale application
docker-compose up -d --scale app=3

# Stop services
docker-compose down

# Remove everything including volumes
docker-compose down -v
```

## Manual Deployment

### 1. Clone Repository
```bash
cd /opt/akcn
sudo -u akcn git clone <repository-url> backend
cd backend
```

### 2. Setup Python Environment
```bash
# Create virtual environment
sudo -u akcn python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Set production values
DATABASE_URL=postgresql+asyncpg://akcn_user:password@localhost:5432/akcn_prod_db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=<generate-strong-secret>
ENVIRONMENT=production
DEBUG=False
```

### 4. Initialize Database
```bash
# Run migrations
alembic upgrade head

# Initialize with production data
python setup_postgresql.py --no-data
```

### 5. Setup Systemd Service
```ini
# /etc/systemd/system/akcn-backend.service
[Unit]
Description=AKCN Backend API Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=akcn
Group=akcn
WorkingDirectory=/opt/akcn/backend
Environment="PATH=/opt/akcn/backend/venv/bin"
ExecStart=/opt/akcn/backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/akcn/access.log \
    --error-logfile /var/log/akcn/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6. Start Service
```bash
# Create log directory
sudo mkdir -p /var/log/akcn
sudo chown -R akcn:akcn /var/log/akcn

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable akcn-backend
sudo systemctl start akcn-backend

# Check status
sudo systemctl status akcn-backend
```

## Cloud Deployment

### AWS EC2 Deployment

#### 1. Launch EC2 Instance
```bash
# Recommended instance types:
# - Development: t3.medium (2 vCPU, 4GB RAM)
# - Production: t3.large or c5.large (2 vCPU, 8GB RAM)

# Security Group Rules:
# - SSH (22): Your IP
# - HTTP (80): 0.0.0.0/0
# - HTTPS (443): 0.0.0.0/0
# - Custom TCP (8000): VPC CIDR (for health checks)
```

#### 2. Setup Instance
```bash
# Connect to instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install dependencies
sudo yum update -y
sudo yum install -y python3 python3-pip git postgresql14
sudo amazon-linux-extras install nginx1

# Follow manual deployment steps
```

#### 3. Setup RDS PostgreSQL
```bash
# Create RDS instance:
# - Engine: PostgreSQL 14
# - Instance Class: db.t3.medium
# - Storage: 20GB SSD
# - Enable automated backups
# - Enable encryption

# Update .env with RDS endpoint
DATABASE_URL=postgresql+asyncpg://username:password@rds-endpoint:5432/akcn_db
```

### Azure App Service Deployment

#### 1. Create Resources
```bash
# Create resource group
az group create --name akcn-rg --location eastus

# Create App Service Plan
az appservice plan create --name akcn-plan --resource-group akcn-rg --sku B2 --is-linux

# Create Web App
az webapp create --resource-group akcn-rg --plan akcn-plan --name akcn-api --runtime "PYTHON:3.10"

# Create PostgreSQL
az postgres server create --resource-group akcn-rg --name akcn-db-server \
    --admin-user akcn_admin --admin-password <password> \
    --sku-name B_Gen5_1 --version 14
```

#### 2. Deploy Application
```bash
# Configure deployment source
az webapp deployment source config --name akcn-api --resource-group akcn-rg \
    --repo-url <git-repo-url> --branch main --manual-integration

# Set environment variables
az webapp config appsettings set --resource-group akcn-rg --name akcn-api --settings \
    DATABASE_URL="postgresql+asyncpg://..." \
    JWT_SECRET_KEY="..." \
    ENVIRONMENT="production"
```

### Kubernetes Deployment

#### 1. Create Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: akcn-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: akcn-backend
  template:
    metadata:
      labels:
        app: akcn-backend
    spec:
      containers:
      - name: app
        image: your-registry/akcn-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: akcn-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: akcn-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/db
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 2. Create Service
```yaml
# k8s-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: akcn-backend-service
spec:
  selector:
    app: akcn-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 3. Deploy to Kubernetes
```bash
# Create secrets
kubectl create secret generic akcn-secrets \
    --from-literal=database-url='postgresql+asyncpg://...' \
    --from-literal=jwt-secret='...'

# Apply configurations
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml

# Check status
kubectl get pods
kubectl get service akcn-backend-service
```

## Configuration

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/akcn
upstream akcn_backend {
    server 127.0.0.1:8000;
    # Add more servers for load balancing
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://akcn_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if any)
    location /static {
        alias /opt/akcn/backend/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://akcn_backend/health;
        access_log off;
    }
}
```

### Environment Variables
```bash
# Production .env configuration
# Database
DATABASE_URL=postgresql+asyncpg://akcn_user:strong_password@localhost:5432/akcn_prod_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Security
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
PASSWORD_MIN_LENGTH=12

# Application
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=["https://app.your-domain.com"]
ALLOWED_HOSTS=["api.your-domain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/hour
RATE_LIMIT_ADMIN=1000/hour

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
PROMETHEUS_ENABLED=true

# Email (if needed)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@your-domain.com
SMTP_PASSWORD=xxx
```

## SSL/TLS Setup

### Using Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run

# Add to crontab
0 0 * * * /usr/bin/certbot renew --quiet
```

### Using Custom Certificate
```bash
# Copy certificates
sudo cp your-cert.crt /etc/ssl/certs/
sudo cp your-key.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/your-key.key

# Update Nginx configuration
ssl_certificate /etc/ssl/certs/your-cert.crt;
ssl_certificate_key /etc/ssl/private/your-key.key;
```

## Monitoring Setup

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'akcn-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "AKCN Backend Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~'5..'}[5m])"
          }
        ]
      }
    ]
  }
}
```

### Application Logs
```python
# Configure structured logging
import logging
from pythonjsonlogger import jsonlogger

# Setup JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

## Backup and Recovery

### Database Backup
```bash
#!/bin/bash
# backup.sh

# Configuration
BACKUP_DIR="/backup/postgresql"
DB_NAME="akcn_prod_db"
DB_USER="akcn_user"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/postgresql/
```

### Restore Database
```bash
# Restore from backup
gunzip -c backup_20241215_120000.sql.gz | psql -U akcn_user -d akcn_prod_db

# Restore specific tables
pg_restore -U akcn_user -d akcn_prod_db -t applications backup.dump
```

### Application Backup
```bash
# Backup application files
tar -czf /backup/app_$(date +%Y%m%d).tar.gz /opt/akcn/backend \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='__pycache__'
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U akcn_user -d akcn_prod_db

# Check logs
tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 2. High Memory Usage
```bash
# Check memory usage
free -h
ps aux | grep python

# Adjust Gunicorn workers
# Calculate: (2 * CPU cores) + 1
gunicorn --workers 3 --worker-class uvicorn.workers.UvicornWorker
```

#### 3. Slow Response Times
```bash
# Check database queries
SELECT query, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;

# Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  # Log queries > 1s
SELECT pg_reload_conf();
```

#### 4. SSL Certificate Issues
```bash
# Test SSL certificate
openssl s_client -connect api.your-domain.com:443 -servername api.your-domain.com

# Check certificate expiry
echo | openssl s_client -connect api.your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Performance Tuning

#### PostgreSQL Tuning
```sql
-- Optimize for your hardware
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET work_mem = '10MB';
ALTER SYSTEM SET max_connections = 200;

-- Reload configuration
SELECT pg_reload_conf();
```

#### Application Tuning
```python
# Optimize database pool
DATABASE_POOL_SIZE = 20  # Adjust based on load
DATABASE_MAX_OVERFLOW = 40
DATABASE_POOL_TIMEOUT = 30

# Enable response caching
from fastapi_cache import FastAPICache
from fastapi_cache.backend.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

## Security Hardening

### 1. System Security
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Enable firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Install fail2ban
sudo apt install fail2ban
```

### 2. Application Security
```python
# Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# CORS configuration
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 3. Database Security
```sql
-- Revoke unnecessary privileges
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Create read-only user for reporting
CREATE USER akcn_readonly WITH PASSWORD 'password';
GRANT CONNECT ON DATABASE akcn_prod_db TO akcn_readonly;
GRANT USAGE ON SCHEMA public TO akcn_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO akcn_readonly;
```

## Maintenance

### Regular Tasks
- **Daily**: Check logs, monitor alerts
- **Weekly**: Review performance metrics, update dependencies
- **Monthly**: Security updates, backup verification
- **Quarterly**: Performance review, capacity planning

### Health Checks
```bash
# Create monitoring script
#!/bin/bash
# health_check.sh

# Check API
curl -f http://localhost:8000/health || echo "API is down"

# Check database
psql -U akcn_user -d akcn_prod_db -c "SELECT 1" || echo "Database is down"

# Check disk space
df -h | grep -E '^/dev/' | awk '{if ($5+0 > 80) print "Warning: "$6" is "$5" full"}'

# Check memory
free -m | awk 'NR==2{printf "Memory Usage: %.2f%%\n", $3*100/$2}'
```

---
*Last Updated: December 2024*
*Version: 1.0.0*