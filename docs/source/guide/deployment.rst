Deployment Guide
================

This comprehensive guide covers deploying the AI Search Engine to production environments.

.. contents:: Table of Contents
   :local:
   :depth: 3

Overview
--------

Deployment Options
~~~~~~~~~~~~~~~~~~

The AI Search Engine supports multiple deployment methods:

* **Docker Compose**: Quick single-server deployment
* **Kubernetes**: Scalable container orchestration
* **Systemd**: Traditional Linux service
* **Cloud Platforms**: AWS, GCP, Azure
* **Serverless**: AWS Lambda, Google Cloud Run

Recommended for Production
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Small Scale** (< 1000 users): Docker Compose on single server
* **Medium Scale** (< 10,000 users): Kubernetes cluster (3-5 nodes)
* **Large Scale** (> 10,000 users): Kubernetes + Auto-scaling + CDN

Prerequisites
-------------

System Requirements
~~~~~~~~~~~~~~~~~~~

**Minimum**:

* CPU: 2 cores
* RAM: 4 GB
* Disk: 50 GB SSD
* Network: 100 Mbps

**Recommended**:

* CPU: 4+ cores
* RAM: 8+ GB
* Disk: 100+ GB SSD
* Network: 1 Gbps

Software Requirements
~~~~~~~~~~~~~~~~~~~~~

* Python 3.10, 3.11, or 3.12
* Docker 20.10+ (for containerized deployment)
* PostgreSQL 14+ or SQLite (for database)
* Redis 6+ (for caching, optional but recommended)
* Nginx or similar (for reverse proxy)

SSL/TLS Certificate
~~~~~~~~~~~~~~~~~~~

For production, you need valid SSL certificates:

* **Let's Encrypt**: Free automated certificates
* **CloudFlare**: Free with CDN
* **Commercial CA**: For enterprise requirements

API Keys
~~~~~~~~

Required API keys (at minimum):

* **LLM Provider**: OpenAI, Aliyun DashScope, or Ollama (local)
* **Search**: SerpAPI (for research mode)

Optional API keys:

* Google API (for Gemini Vision)
* OpenWeatherMap (for weather queries)
* Alpha Vantage (for finance queries)
* OpenRouteService (for routing queries)

Docker Deployment
-----------------

Quick Start with Docker Compose
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Step 1: Create Deployment Directory**

.. code-block:: bash

   mkdir -p /opt/ai-search
   cd /opt/ai-search

**Step 2: Create docker-compose.yml**

.. code-block:: yaml

   version: '3.8'

   services:
     app:
       image: ai-search:latest
       container_name: ai-search-app
       restart: unless-stopped
       ports:
         - "8000:8000"
       environment:
         - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
         - SERPAPI_API_KEY=${SERPAPI_API_KEY}
         - DATABASE_URL=postgresql://user:pass@db:5432/aisearch
         - REDIS_URL=redis://redis:6379/0
         - WEB_HOST=0.0.0.0
         - WEB_PORT=8000
         - WEB_WORKERS=4
       volumes:
         - ./data:/app/data
         - ./uploads:/app/uploads
         - ./logs:/app/logs
       depends_on:
         - db
         - redis
       networks:
         - ai-search-network

     db:
       image: postgres:14-alpine
       container_name: ai-search-db
       restart: unless-stopped
       environment:
         - POSTGRES_USER=aisearch
         - POSTGRES_PASSWORD=${DB_PASSWORD}
         - POSTGRES_DB=aisearch
       volumes:
         - postgres-data:/var/lib/postgresql/data
       networks:
         - ai-search-network

     redis:
       image: redis:7-alpine
       container_name: ai-search-redis
       restart: unless-stopped
       command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
       volumes:
         - redis-data:/data
       networks:
         - ai-search-network

     nginx:
       image: nginx:alpine
       container_name: ai-search-nginx
       restart: unless-stopped
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
         - ./nginx/ssl:/etc/nginx/ssl:ro
       depends_on:
         - app
       networks:
         - ai-search-network

   volumes:
     postgres-data:
     redis-data:

   networks:
     ai-search-network:
       driver: bridge

**Step 3: Create .env File**

.. code-block:: bash

   # .env
   DASHSCOPE_API_KEY=sk-your-key-here
   SERPAPI_API_KEY=your-serpapi-key
   DB_PASSWORD=your-secure-password-here
   OPENAI_API_KEY=sk-your-openai-key  # Optional
   GOOGLE_API_KEY=your-google-key  # Optional

**Step 4: Build and Run**

.. code-block:: bash

   # Build image
   docker build -t ai-search:latest .

   # Start services
   docker-compose up -d

   # Check logs
   docker-compose logs -f app

   # Check status
   docker-compose ps

**Step 5: Verify Deployment**

.. code-block:: bash

   # Health check
   curl http://localhost:8000/health

   # Expected response:
   # {"status": "healthy", "version": "1.0.0"}

Dockerfile
~~~~~~~~~~

Create optimized Dockerfile:

.. code-block:: dockerfile

   # Use official Python runtime
   FROM python:3.11-slim

   # Set working directory
   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \\
       gcc \\
       g++ \\
       libpq-dev \\
       curl \\
       && rm -rf /var/lib/apt/lists/*

   # Copy requirements and install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY src/ ./src/
   COPY config/ ./config/
   COPY data/ ./data/

   # Create non-root user
   RUN useradd -m -u 1000 appuser && \\
       chown -R appuser:appuser /app
   USER appuser

   # Expose port
   EXPOSE 8000

   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
       CMD curl -f http://localhost:8000/health || exit 1

   # Run application
   CMD ["uvicorn", "src.web.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

Multi-Stage Build (Production)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For smaller images:

.. code-block:: dockerfile

   # Build stage
   FROM python:3.11-slim as builder

   WORKDIR /app
   COPY requirements.txt .

   RUN pip install --user --no-cache-dir -r requirements.txt

   # Runtime stage
   FROM python:3.11-slim

   WORKDIR /app

   # Copy Python dependencies from builder
   COPY --from=builder /root/.local /root/.local

   # Copy application
   COPY src/ ./src/
   COPY config/ ./config/

   # Update PATH
   ENV PATH=/root/.local/bin:$PATH

   EXPOSE 8000

   CMD ["uvicorn", "src.web.app:app", "--host", "0.0.0.0", "--port", "8000"]

Nginx Configuration
~~~~~~~~~~~~~~~~~~~

Create ``nginx/nginx.conf``:

.. code-block:: nginx

   events {
       worker_connections 1024;
   }

   http {
       upstream app {
           server app:8000;
       }

       # Rate limiting
       limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/m;

       server {
           listen 80;
           server_name your-domain.com;

           # Redirect to HTTPS
           return 301 https://$server_name$request_uri;
       }

       server {
           listen 443 ssl http2;
           server_name your-domain.com;

           # SSL configuration
           ssl_certificate /etc/nginx/ssl/cert.pem;
           ssl_certificate_key /etc/nginx/ssl/key.pem;
           ssl_protocols TLSv1.2 TLSv1.3;
           ssl_ciphers HIGH:!aNULL:!MD5;

           # Security headers
           add_header Strict-Transport-Security "max-age=31536000" always;
           add_header X-Frame-Options "SAMEORIGIN" always;
           add_header X-Content-Type-Options "nosniff" always;
           add_header X-XSS-Protection "1; mode=block" always;

           # Logging
           access_log /var/log/nginx/ai-search-access.log;
           error_log /var/log/nginx/ai-search-error.log;

           # Max upload size
           client_max_body_size 100M;

           location / {
               proxy_pass http://app;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;

               # Timeouts
               proxy_connect_timeout 60s;
               proxy_send_timeout 60s;
               proxy_read_timeout 60s;
           }

           # Rate limiting for API endpoints
           location /query {
               limit_req zone=api_limit burst=10 nodelay;
               proxy_pass http://app;
           }

           # Static files (if any)
           location /static {
               alias /app/static;
               expires 1y;
               add_header Cache-Control "public, immutable";
           }
       }
   }

Kubernetes Deployment
---------------------

Kubernetes Manifests
~~~~~~~~~~~~~~~~~~~~

**1. Namespace**

.. code-block:: yaml

   # namespace.yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: ai-search

**2. ConfigMap**

.. code-block:: yaml

   # configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: ai-search-config
     namespace: ai-search
   data:
     WEB_HOST: "0.0.0.0"
     WEB_PORT: "8000"
     WEB_WORKERS: "4"
     LOG_LEVEL: "INFO"

**3. Secret**

.. code-block:: yaml

   # secret.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: ai-search-secrets
     namespace: ai-search
   type: Opaque
   stringData:
     DASHSCOPE_API_KEY: "your-key-here"
     SERPAPI_API_KEY: "your-key-here"
     DB_PASSWORD: "your-password-here"

**4. Deployment**

.. code-block:: yaml

   # deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: ai-search-app
     namespace: ai-search
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: ai-search
     template:
       metadata:
         labels:
           app: ai-search
       spec:
         containers:
         - name: app
           image: ai-search:latest
           ports:
           - containerPort: 8000
           env:
           - name: WEB_HOST
             valueFrom:
               configMapKeyRef:
                 name: ai-search-config
                 key: WEB_HOST
           - name: DASHSCOPE_API_KEY
             valueFrom:
               secretKeyRef:
                 name: ai-search-secrets
                 key: DASHSCOPE_API_KEY
           resources:
             requests:
               memory: "2Gi"
               cpu: "1000m"
             limits:
               memory: "4Gi"
               cpu: "2000m"
           livenessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 5
             periodSeconds: 5

**5. Service**

.. code-block:: yaml

   # service.yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: ai-search-service
     namespace: ai-search
   spec:
     selector:
       app: ai-search
     ports:
     - protocol: TCP
       port: 80
       targetPort: 8000
     type: LoadBalancer

**6. Ingress**

.. code-block:: yaml

   # ingress.yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: ai-search-ingress
     namespace: ai-search
     annotations:
       cert-manager.io/cluster-issuer: letsencrypt-prod
       nginx.ingress.kubernetes.io/rate-limit: "30"
   spec:
     ingressClassName: nginx
     tls:
     - hosts:
       - ai-search.example.com
       secretName: ai-search-tls
     rules:
     - host: ai-search.example.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: ai-search-service
               port:
                 number: 80

**7. HorizontalPodAutoscaler**

.. code-block:: yaml

   # hpa.yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: ai-search-hpa
     namespace: ai-search
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: ai-search-app
     minReplicas: 3
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
     - type: Resource
       resource:
         name: memory
         target:
           type: Utilization
           averageUtilization: 80

Deploy to Kubernetes
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Apply manifests
   kubectl apply -f namespace.yaml
   kubectl apply -f configmap.yaml
   kubectl apply -f secret.yaml
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   kubectl apply -f ingress.yaml
   kubectl apply -f hpa.yaml

   # Check status
   kubectl get pods -n ai-search
   kubectl get svc -n ai-search
   kubectl get ingress -n ai-search

   # View logs
   kubectl logs -f deployment/ai-search-app -n ai-search

   # Scale manually
   kubectl scale deployment ai-search-app --replicas=5 -n ai-search

Helm Chart
~~~~~~~~~~

Create Helm chart for easier management:

.. code-block:: bash

   # Create chart
   helm create ai-search

   # Install
   helm install ai-search ./ai-search \\
     --namespace ai-search \\
     --create-namespace \\
     --set image.tag=latest \\
     --set replicas=3

   # Upgrade
   helm upgrade ai-search ./ai-search

   # Rollback
   helm rollback ai-search

Systemd Service
---------------

For traditional Linux deployment without containers.

Create Service File
~~~~~~~~~~~~~~~~~~~

Create ``/etc/systemd/system/ai-search.service``:

.. code-block:: ini

   [Unit]
   Description=AI Search Engine
   After=network.target postgresql.service redis.service
   Wants=postgresql.service redis.service

   [Service]
   Type=notify
   User=aisearch
   Group=aisearch
   WorkingDirectory=/opt/ai-search
   Environment="PATH=/opt/ai-search/venv/bin:/usr/local/bin:/usr/bin"
   EnvironmentFile=/opt/ai-search/.env

   ExecStart=/opt/ai-search/venv/bin/uvicorn src.web.app:app \\
     --host 0.0.0.0 \\
     --port 8000 \\
     --workers 4 \\
     --log-level info

   # Restart policy
   Restart=always
   RestartSec=10

   # Security
   NoNewPrivileges=true
   PrivateTmp=true
   ProtectSystem=strict
   ProtectHome=true
   ReadWritePaths=/opt/ai-search/data /opt/ai-search/uploads /opt/ai-search/logs

   # Resource limits
   LimitNOFILE=65536
   LimitNPROC=4096

   [Install]
   WantedBy=multi-user.target

Installation Steps
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create user
   sudo useradd -r -s /bin/false aisearch

   # Create directories
   sudo mkdir -p /opt/ai-search
   sudo chown aisearch:aisearch /opt/ai-search

   # Deploy application
   cd /opt/ai-search
   sudo -u aisearch python3 -m venv venv
   sudo -u aisearch venv/bin/pip install -r requirements.txt
   sudo -u aisearch cp -r src config data /opt/ai-search/

   # Create .env file
   sudo -u aisearch nano /opt/ai-search/.env

   # Enable and start service
   sudo systemctl daemon-reload
   sudo systemctl enable ai-search
   sudo systemctl start ai-search

   # Check status
   sudo systemctl status ai-search

   # View logs
   sudo journalctl -u ai-search -f

Cloud Platform Deployment
--------------------------

AWS Deployment
~~~~~~~~~~~~~~

**Using AWS ECS (Elastic Container Service)**

1. **Create ECR Repository**

.. code-block:: bash

   aws ecr create-repository --repository-name ai-search

2. **Build and Push Image**

.. code-block:: bash

   # Login to ECR
   aws ecr get-login-password --region us-east-1 | \\
     docker login --username AWS --password-stdin \\
     123456789.dkr.ecr.us-east-1.amazonaws.com

   # Build
   docker build -t ai-search:latest .

   # Tag
   docker tag ai-search:latest \\
     123456789.dkr.ecr.us-east-1.amazonaws.com/ai-search:latest

   # Push
   docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/ai-search:latest

3. **Create ECS Task Definition**

.. code-block:: json

   {
     "family": "ai-search",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "2048",
     "memory": "4096",
     "containerDefinitions": [
       {
         "name": "app",
         "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/ai-search:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {"name": "WEB_HOST", "value": "0.0.0.0"},
           {"name": "WEB_PORT", "value": "8000"}
         ],
         "secrets": [
           {
             "name": "DASHSCOPE_API_KEY",
             "valueFrom": "arn:aws:secretsmanager:us-east-1:123:secret:dashscope"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/ai-search",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }

4. **Create ECS Service**

.. code-block:: bash

   aws ecs create-service \\
     --cluster ai-search-cluster \\
     --service-name ai-search-service \\
     --task-definition ai-search \\
     --desired-count 3 \\
     --launch-type FARGATE \\
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \\
     --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=app,containerPort=8000"

GCP Deployment
~~~~~~~~~~~~~~

**Using Google Cloud Run**

.. code-block:: bash

   # Build and push to GCR
   gcloud builds submit --tag gcr.io/PROJECT_ID/ai-search

   # Deploy
   gcloud run deploy ai-search \\
     --image gcr.io/PROJECT_ID/ai-search \\
     --platform managed \\
     --region us-central1 \\
     --allow-unauthenticated \\
     --memory 4Gi \\
     --cpu 2 \\
     --max-instances 10 \\
     --set-env-vars WEB_HOST=0.0.0.0,WEB_PORT=8080 \\
     --set-secrets DASHSCOPE_API_KEY=dashscope-key:latest

Azure Deployment
~~~~~~~~~~~~~~~~

**Using Azure Container Instances**

.. code-block:: bash

   # Create resource group
   az group create --name ai-search-rg --location eastus

   # Create container
   az container create \\
     --resource-group ai-search-rg \\
     --name ai-search \\
     --image yourregistry.azurecr.io/ai-search:latest \\
     --cpu 2 \\
     --memory 4 \\
     --ports 8000 \\
     --environment-variables WEB_HOST=0.0.0.0 WEB_PORT=8000 \\
     --secure-environment-variables DASHSCOPE_API_KEY=your-key

Security Hardening
------------------

Application Security
~~~~~~~~~~~~~~~~~~~~

1. **Environment Variables**

.. code-block:: bash

   # Never commit secrets to git
   # Use .env files (add to .gitignore)
   # Or use secret management services

2. **Enable Docker Sandbox**

.. code-block:: yaml

   # config/config.yaml
   code_execution:
     enable_docker: true
     docker_memory_limit: 512m
     docker_cpu_limit: 1.0

3. **API Key Authentication**

.. code-block:: yaml

   security:
     enable_api_key_auth: true
     api_keys:
       - ${API_KEY_1}
       - ${API_KEY_2}

4. **Rate Limiting**

.. code-block:: yaml

   web:
     rate_limiting:
       enabled: true
       requests_per_minute: 30

Network Security
~~~~~~~~~~~~~~~~

1. **HTTPS Only**

.. code-block:: nginx

   server {
       listen 80;
       return 301 https://$server_name$request_uri;
   }

2. **Security Headers**

.. code-block:: nginx

   add_header Strict-Transport-Security "max-age=31536000";
   add_header X-Frame-Options "SAMEORIGIN";
   add_header X-Content-Type-Options "nosniff";
   add_header X-XSS-Protection "1; mode=block";

3. **Firewall Rules**

.. code-block:: bash

   # Allow only necessary ports
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable

Database Security
~~~~~~~~~~~~~~~~~

1. **Strong Passwords**

.. code-block:: bash

   # Generate secure password
   openssl rand -base64 32

2. **Encrypted Connections**

.. code-block:: yaml

   database:
     url: postgresql://user:pass@host:5432/db?sslmode=require

3. **Regular Backups**

.. code-block:: bash

   # Automated backup script
   #!/bin/bash
   pg_dump -U aisearch aisearch > backup-$(date +%Y%m%d).sql
   aws s3 cp backup-$(date +%Y%m%d).sql s3://backups/

Monitoring and Logging
----------------------

Health Checks
~~~~~~~~~~~~~

.. code-block:: bash

   # Application health
   curl http://localhost:8000/health

   # Expected response
   {"status": "healthy", "version": "1.0.0"}

Prometheus Metrics
~~~~~~~~~~~~~~~~~~

Add metrics endpoint:

.. code-block:: python

   from prometheus_client import Counter, Histogram
   from fastapi import FastAPI

   REQUEST_COUNT = Counter('requests_total', 'Total requests')
   REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency')

   @app.middleware("http")
   async def metrics_middleware(request, call_next):
       REQUEST_COUNT.inc()
       with REQUEST_LATENCY.time():
           response = await call_next(request)
       return response

Logging Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # config/config.yaml
   logging:
     level: INFO
     format: json
     file: /var/log/ai-search/app.log
     max_bytes: 10485760  # 10MB
     backup_count: 5

Log Aggregation
~~~~~~~~~~~~~~~

**Using ELK Stack**:

.. code-block:: yaml

   # docker-compose.yml
   elasticsearch:
     image: elasticsearch:8.10.0

   logstash:
     image: logstash:8.10.0
     volumes:
       - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

   kibana:
     image: kibana:8.10.0
     ports:
       - "5601:5601"

**Using Loki + Grafana**:

.. code-block:: bash

   # Install Loki
   docker run -d --name=loki -p 3100:3100 grafana/loki

   # Install Grafana
   docker run -d --name=grafana -p 3000:3000 grafana/grafana

Alerting
~~~~~~~~

**Slack Notifications**:

.. code-block:: python

   import requests

   def send_alert(message):
       webhook_url = os.getenv("SLACK_WEBHOOK_URL")
       requests.post(webhook_url, json={"text": message})

**Email Alerts**:

.. code-block:: python

   import smtplib

   def send_email_alert(subject, body):
       # Configure SMTP
       server = smtplib.SMTP('smtp.gmail.com', 587)
       server.starttls()
       server.login(email, password)
       server.sendmail(from_email, to_email, message)

Performance Optimization
------------------------

Application Tuning
~~~~~~~~~~~~~~~~~~

1. **Worker Processes**

.. code-block:: bash

   # Calculate optimal workers
   workers = (2 * cpu_cores) + 1

   # Start with optimal workers
   uvicorn src.web.app:app --workers 9  # For 4 cores

2. **Connection Pooling**

.. code-block:: python

   # database.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=10,
       pool_pre_ping=True
   )

3. **Async Operations**

.. code-block:: python

   # Use async for I/O operations
   async def fetch_data():
       async with aiohttp.ClientSession() as session:
           async with session.get(url) as response:
               return await response.json()

Redis Caching
~~~~~~~~~~~~~

.. code-block:: python

   import redis
   from functools import wraps

   redis_client = redis.Redis(host='localhost', port=6379, db=0)

   def cache_result(ttl=3600):
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               key = f"{func.__name__}:{args}:{kwargs}"
               cached = redis_client.get(key)
               if cached:
                   return json.loads(cached)
               result = await func(*args, **kwargs)
               redis_client.setex(key, ttl, json.dumps(result))
               return result
           return wrapper
       return decorator

CDN Configuration
~~~~~~~~~~~~~~~~~

**CloudFlare**:

1. Add domain to CloudFlare
2. Update DNS records
3. Enable caching for static assets
4. Enable Brotli compression
5. Configure Page Rules

Database Optimization
~~~~~~~~~~~~~~~~~~~~~

1. **Indexes**

.. code-block:: sql

   CREATE INDEX idx_timestamp ON conversation_history(timestamp);
   CREATE INDEX idx_mode ON conversation_history(mode);
   CREATE INDEX idx_hash ON rag_documents(file_hash);

2. **Query Optimization**

.. code-block:: sql

   -- Use EXPLAIN to analyze queries
   EXPLAIN ANALYZE SELECT * FROM conversation_history WHERE mode='research';

   -- Add appropriate indexes
   CREATE INDEX idx_mode_timestamp ON conversation_history(mode, timestamp);

Backup and Recovery
-------------------

Database Backup
~~~~~~~~~~~~~~~

**Automated Backup Script**:

.. code-block:: bash

   #!/bin/bash
   # backup.sh

   DATE=$(date +%Y%m%d_%H%M%S)
   BACKUP_DIR="/backups"
   DB_NAME="aisearch"

   # Create backup
   pg_dump -U postgres $DB_NAME > $BACKUP_DIR/db_$DATE.sql

   # Compress
   gzip $BACKUP_DIR/db_$DATE.sql

   # Upload to S3
   aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://my-backups/database/

   # Keep only last 30 days
   find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

**Cron Job**:

.. code-block:: bash

   # Daily backup at 2 AM
   0 2 * * * /opt/ai-search/backup.sh

Application Backup
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # Backup uploaded files and vector store

   rsync -av /opt/ai-search/uploads/ /backups/uploads/
   rsync -av /opt/ai-search/data/vector_store/ /backups/vector_store/

Disaster Recovery
~~~~~~~~~~~~~~~~~

**Recovery Plan**:

1. **Database Recovery**

.. code-block:: bash

   # Restore from backup
   gunzip < backup.sql.gz | psql -U postgres aisearch

2. **Application Recovery**

.. code-block:: bash

   # Restore files
   rsync -av /backups/uploads/ /opt/ai-search/uploads/
   rsync -av /backups/vector_store/ /opt/ai-search/data/vector_store/

   # Restart services
   docker-compose restart

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**1. Application won't start**

.. code-block:: bash

   # Check logs
   docker-compose logs app

   # Common causes:
   # - Missing environment variables
   # - Database connection failed
   # - Port already in use

**2. High memory usage**

.. code-block:: bash

   # Check memory
   docker stats

   # Solutions:
   # - Reduce worker count
   # - Enable memory limits
   # - Optimize vector store cache

**3. Slow response times**

.. code-block:: bash

   # Check metrics
   curl http://localhost:8000/metrics

   # Solutions:
   # - Enable Redis caching
   # - Optimize database queries
   # - Scale horizontally

**4. SSL certificate errors**

.. code-block:: bash

   # Renew Let's Encrypt certificate
   certbot renew

   # Or manual renewal
   certbot certonly --webroot -w /var/www/html -d your-domain.com

Debugging
~~~~~~~~~

.. code-block:: bash

   # Enable debug logging
   export LOG_LEVEL=DEBUG
   docker-compose restart app

   # Check application logs
   docker-compose logs -f app

   # Check database logs
   docker-compose logs -f db

   # Check network
   docker network inspect ai-search-network

Maintenance
-----------

Regular Maintenance Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~

**Daily**:
- Monitor health endpoint
- Check error logs
- Verify backups completed

**Weekly**:
- Review performance metrics
- Check disk space
- Update dependencies (if needed)

**Monthly**:
- Database vacuum/analyze
- Review and optimize queries
- Update SSL certificates (if expiring)
- Security audit

Update Procedure
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Backup current state
   docker-compose exec app python -m src.main info > pre-update-info.txt
   ./backup.sh

   # 2. Pull new code
   git pull origin main

   # 3. Build new image
   docker-compose build

   # 4. Rolling update (zero downtime)
   docker-compose up -d --no-deps --build app

   # 5. Verify health
   curl http://localhost:8000/health

   # 6. If issues, rollback
   docker-compose down
   git checkout previous-version
   docker-compose up -d

Scaling Guide
~~~~~~~~~~~~~

**Vertical Scaling** (Increase resources):

.. code-block:: yaml

   # docker-compose.yml
   services:
     app:
       deploy:
         resources:
           limits:
             cpus: '4'
             memory: 8G

**Horizontal Scaling** (More instances):

.. code-block:: bash

   # Kubernetes
   kubectl scale deployment ai-search-app --replicas=10

   # Docker Compose
   docker-compose up -d --scale app=4

Checklist
---------

Pre-Deployment
~~~~~~~~~~~~~~

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database migrations tested
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Load testing completed

Post-Deployment
~~~~~~~~~~~~~~~

- [ ] Health check passing
- [ ] Logs being collected
- [ ] Metrics being reported
- [ ] Backups running automatically
- [ ] SSL certificate valid
- [ ] DNS configured correctly
- [ ] Rate limiting working
- [ ] Error tracking enabled

Security Checklist
~~~~~~~~~~~~~~~~~~

- [ ] API keys in environment variables
- [ ] Docker sandbox enabled for code execution
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Database encrypted
- [ ] Regular security updates scheduled

Conclusion
----------

This guide covers comprehensive deployment options for the AI Search Engine. Choose the deployment method that best fits your requirements:

- **Small projects**: Docker Compose
- **Medium projects**: Kubernetes
- **Enterprise**: Cloud platforms with auto-scaling

Remember to:

1. Always use HTTPS in production
2. Enable all security features
3. Set up monitoring and alerting
4. Implement regular backups
5. Plan for scaling

For additional help, see:

- :doc:`configuration` for detailed configuration options
- :doc:`installation` for setup instructions
- :doc:`/dev/architecture` for system architecture
- GitHub Issues for community support
