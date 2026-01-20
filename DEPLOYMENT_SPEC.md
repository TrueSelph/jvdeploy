# jvbundler Deployment Specification v1.0

## Executive Summary

Extend jvbundler to support end-to-end deployment to AWS Lambda and Kubernetes using a **unified Dockerfile**. The tool will handle building, pushing, and deploying jvagent applications to both platforms with a single, declarative configuration.

## Design Principles

1. **Unified Dockerfile**: Single Dockerfile works for both Lambda and Kubernetes
2. **Declarative Configuration**: Use YAML configuration for deployment settings
3. **Platform Abstraction**: Abstract platform-specific details behind common interface
4. **Progressive Enhancement**: Start with basic deployment, add advanced features incrementally
5. **Security First**: Handle credentials securely, support IAM roles and ServiceAccounts
6. **Idempotent Operations**: Deployments should be safe to run multiple times
7. **Developer Experience**: Simple commands for common workflows

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    jvbundler CLI                        │
├─────────────────────────────────────────────────────────┤
│  bundle  │  deploy lambda  │  deploy k8s  │  init      │
└──────────┴─────────────────┴──────────────┴────────────┘
     │            │                  │
     ▼            ▼                  ▼
┌─────────┐  ┌─────────────┐  ┌─────────────┐
│Dockerfile│  │   Lambda    │  │ Kubernetes  │
│Generator│  │  Deployer   │  │  Deployer   │
└─────────┘  └─────────────┘  └─────────────┘
                  │                  │
                  ▼                  ▼
           ┌─────────────┐    ┌─────────────┐
           │ AWS Stack   │    │ K8s Stack   │
           │ - ECR       │    │ - Registry  │
           │ - Lambda    │    │ - Deployment│
           │ - API GW    │    │ - Service   │
           └─────────────┘    │ - ConfigMap │
                              └─────────────┘
```

## Unified Dockerfile Strategy

### Approach: AWS Lambda Web Adapter (Recommended)

Use AWS Lambda Web Adapter to make any HTTP server work seamlessly in both Lambda and Kubernetes:

**Benefits:**
- Single Dockerfile for both platforms
- No runtime detection needed
- Standard HTTP server works everywhere
- Simple and maintainable

**Updated Dockerfile.base:**

```dockerfile
# Multi-platform support: Lambda + Kubernetes
FROM python:3.12-slim

# Copy Lambda Web Adapter for Lambda compatibility
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /var/task

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /var/task/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# {{ACTION_DEPENDENCIES}}

# Expose port for HTTP server
EXPOSE 8080

# Environment variables for Lambda Web Adapter
ENV PORT=8080
ENV AWS_LWA_INVOKE_MODE=response_stream
ENV AWS_LWA_READINESS_CHECK_PATH=/health
ENV AWS_LWA_READINESS_CHECK_PORT=8080

# Health check (works in both Lambda and K8s)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the HTTP server (works in both Lambda and K8s)
CMD ["python", "-m", "uvicorn", "jvagent.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

**How it works:**
- **In Lambda**: Lambda Web Adapter intercepts Lambda invocations and forwards them as HTTP requests to your server on port 8080
- **In Kubernetes**: Standard HTTP server listens on port 8080, no adapter needed
- **Same code, same Dockerfile, different runtime environment**

## Configuration Format

### deploy.yaml

```yaml
# jvbundler deployment configuration
version: "1.0"

# Application metadata
app:
  name: my-jvagent-app
  version: "1.0.0"
  description: "My jvagent application"

# Docker image configuration
image:
  name: my-jvagent-app
  tag: "{{version}}"  # Template support
  build:
    platform: linux/amd64
    cache: true
    args:
      PYTHON_VERSION: "3.12"

# AWS Lambda deployment configuration
lambda:
  enabled: true
  
  # AWS Configuration
  region: us-east-1
  account_id: "123456789012"  # Optional, auto-detected
  
  # Lambda Function
  function:
    name: "{{app.name}}"
    description: "{{app.description}}"
    memory: 1024  # MB (128-10240)
    timeout: 300  # seconds (1-900)
    architecture: x86_64  # x86_64 or arm64
    ephemeral_storage: 512  # MB (512-10240)
    
  # ECR Repository
  ecr:
    repository_name: "{{app.name}}"
    create_if_missing: true
    
  # Environment variables
  environment:
    JVAGENT_ADMIN_PASSWORD: "${JVAGENT_ADMIN_PASSWORD}"  # From env
    JVSPATIAL_DB_TYPE: "json"
    JVSPATIAL_DB_PATH: "/mnt/efs/jvagent_db"
    LOG_LEVEL: "INFO"
    
  # IAM Role
  iam:
    role_arn: null  # null = auto-create
    role_name: "{{app.name}}-lambda-role"
    policies:
      - "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
      - "arn:aws:iam::aws:policy/AmazonElasticFileSystemClientReadWriteAccess"
  
  # VPC Configuration (optional)
  vpc:
    enabled: false
    security_group_ids: []
    subnet_ids: []
    
  # EFS Configuration (optional)
  efs:
    enabled: true
    file_system_id: "fs-1234567890abcdef0"
    access_point_arn: "arn:aws:elasticfilesystem:us-east-1:123456789012:access-point/fsap-1234567890abcdef0"
    mount_path: "/mnt/efs"
    
  # API Gateway Configuration
  api_gateway:
    enabled: true
    type: "HTTP"  # HTTP or REST
    name: "{{app.name}}-api"
    stage_name: "prod"
    cors:
      enabled: true
      allow_origins: ["*"]
      allow_methods: ["*"]
      allow_headers: ["*"]
    throttling:
      rate_limit: 1000
      burst_limit: 2000
    custom_domain:
      enabled: false
      domain_name: "api.example.com"
      certificate_arn: null

# Kubernetes deployment configuration
kubernetes:
  enabled: true
  
  # Cluster Configuration
  context: "my-cluster"  # kubectl context name
  namespace: "default"
  
  # Image Registry
  registry:
    url: "docker.io/myorg"  # Or use ECR
    secret_name: "regcred"  # For private registries
    create_secret: false
    
  # Deployment Configuration
  deployment:
    replicas: 2
    
    strategy:
      type: "RollingUpdate"
      rolling_update:
        max_surge: 1
        max_unavailable: 0
        
    # Pod Configuration
    pod:
      labels:
        app: "{{app.name}}"
        version: "{{app.version}}"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        
    # Container Configuration
    container:
      name: "{{app.name}}"
      port: 8080
      
      # Environment variables
      environment:
        JVAGENT_ADMIN_PASSWORD: "${JVAGENT_ADMIN_PASSWORD}"
        JVSPATIAL_DB_TYPE: "json"
        JVSPATIAL_DB_PATH: "/data/jvagent_db"
        LOG_LEVEL: "INFO"
        
      # Resource limits
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "2000m"
          memory: "2Gi"
          
      # Health checks
      liveness_probe:
        http_get:
          path: "/health"
          port: 8080
        initial_delay_seconds: 30
        period_seconds: 10
        timeout_seconds: 3
        failure_threshold: 3
        
      readiness_probe:
        http_get:
          path: "/ready"
          port: 8080
        initial_delay_seconds: 5
        period_seconds: 5
        timeout_seconds: 2
        failure_threshold: 3
        
  # Service Configuration
  service:
    type: "LoadBalancer"  # ClusterIP, NodePort, LoadBalancer
    port: 80
    target_port: 8080
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
      
  # Ingress Configuration (optional)
  ingress:
    enabled: false
    class_name: "nginx"
    annotations:
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
    rules:
      - host: "my-app.example.com"
        paths:
          - path: "/"
            path_type: "Prefix"
    tls:
      - hosts:
          - "my-app.example.com"
        secret_name: "my-app-tls"
        
  # Persistent Storage (optional)
  persistence:
    enabled: true
    storage_class: "gp2"
    size: "10Gi"
    mount_path: "/data"
    access_modes:
      - "ReadWriteOnce"
      
  # ConfigMap for additional config
  config_map:
    enabled: true
    data:
      app.conf: |
        # Application configuration
        debug: false
        
  # Horizontal Pod Autoscaler (optional)
  autoscaling:
    enabled: false
    min_replicas: 2
    max_replicas: 10
    target_cpu_utilization: 80
    target_memory_utilization: 80
```

## CLI Interface Design

### Main Commands

```bash
# Initialize deployment configuration
jvbundler init [options] [<app_root>]
  --lambda              # Include Lambda configuration
  --kubernetes          # Include Kubernetes configuration
  --all                 # Include both (default)
  --config <file>       # Output file (default: deploy.yaml)

# Deploy to Lambda (end-to-end)
jvbundler deploy lambda [options] [<app_root>]
  --config <file>       # Config file (default: deploy.yaml)
  --build               # Build Docker image
  --push                # Push to ECR
  --update              # Update Lambda function
  --create-api          # Create/update API Gateway
  --all                 # Do all steps (default)
  --region <region>     # Override AWS region
  --function <name>     # Override function name
  --env KEY=VALUE       # Override environment variables
  --dry-run             # Show what would happen
  --debug               # Enable debug logging

# Deploy to Kubernetes (end-to-end)
jvbundler deploy k8s [options] [<app_root>]
  --config <file>       # Config file (default: deploy.yaml)
  --build               # Build Docker image
  --push                # Push to registry
  --apply               # Apply manifests
  --all                 # Do all steps (default)
  --namespace <ns>      # Override namespace
  --context <context>   # Override kubectl context
  --env KEY=VALUE       # Override environment variables
  --dry-run             # Show manifests without applying
  --debug               # Enable debug logging

# Status commands
jvbundler status lambda [options]
  --config <file>
  --function <name>
  --region <region>
  --json                # Output as JSON

jvbundler status k8s [options]
  --config <file>
  --namespace <ns>
  --context <context>
  --json                # Output as JSON

# Logs commands
jvbundler logs lambda [options]
  --function <name>
  --region <region>
  --follow              # Stream logs
  --tail <n>            # Show last n lines
  --since <time>        # Show logs since time

jvbundler logs k8s [options]
  --namespace <ns>
  --pod <pod>           # Specific pod (auto-select if omitted)
  --follow              # Stream logs
  --tail <n>            # Show last n lines
  --since <time>        # Show logs since time

# Destroy/cleanup
jvbundler destroy lambda [options]
  --config <file>
  --function <name>
  --delete-api          # Also delete API Gateway
  --delete-role         # Also delete IAM role
  --yes                 # Skip confirmation

jvbundler destroy k8s [options]
  --config <file>
  --namespace <ns>
  --yes                 # Skip confirmation
```

### Usage Examples

```bash
# 1. Initialize a new jvagent app with deployment config
cd my-jvagent-app
jvbundler init --all

# 2. Deploy to Lambda (complete end-to-end)
jvbundler deploy lambda --all

# 3. Deploy to Kubernetes (complete end-to-end)
jvbundler deploy k8s --all

# 4. Deploy to both platforms
jvbundler deploy lambda --all
jvbundler deploy k8s --all

# 5. Update Lambda function only (no rebuild)
jvbundler deploy lambda --update

# 6. Update Kubernetes deployment only (no rebuild)
jvbundler deploy k8s --apply

# 7. Build and push image without deploying
jvbundler deploy lambda --build --push
jvbundler deploy k8s --build --push  # Can use same image

# 8. Dry run to see what would happen
jvbundler deploy lambda --all --dry-run
jvbundler deploy k8s --all --dry-run

# 9. Deploy with environment overrides
jvbundler deploy lambda --all --env LOG_LEVEL=DEBUG --env FEATURE_FLAG=true

# 10. Check deployment status
jvbundler status lambda
jvbundler status k8s

# 11. View logs
jvbundler logs lambda --follow
jvbundler logs k8s --follow

# 12. Deploy to different regions/namespaces
jvbundler deploy lambda --all --region us-west-2 --function my-app-prod
jvbundler deploy k8s --all --namespace production --context prod-cluster

# 13. Destroy deployments
jvbundler destroy lambda --yes
jvbundler destroy k8s --yes
```

## Kubernetes Manifest Templates

### deployment.yaml.j2

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app.name }}
  namespace: {{ kubernetes.namespace }}
  labels:
    app: {{ app.name }}
    version: {{ app.version }}
spec:
  replicas: {{ kubernetes.deployment.replicas }}
  strategy:
    type: {{ kubernetes.deployment.strategy.type }}
    {% if kubernetes.deployment.strategy.type == "RollingUpdate" %}
    rollingUpdate:
      maxSurge: {{ kubernetes.deployment.strategy.rolling_update.max_surge }}
      maxUnavailable: {{ kubernetes.deployment.strategy.rolling_update.max_unavailable }}
    {% endif %}
  selector:
    matchLabels:
      app: {{ app.name }}
  template:
    metadata:
      labels:
        {% for key, value in kubernetes.deployment.pod.labels.items() %}
        {{ key }}: {{ value }}
        {% endfor %}
      {% if kubernetes.deployment.pod.annotations %}
      annotations:
        {% for key, value in kubernetes.deployment.pod.annotations.items() %}
        {{ key }}: "{{ value }}"
        {% endfor %}
      {% endif %}
    spec:
      {% if kubernetes.registry.secret_name %}
      imagePullSecrets:
        - name: {{ kubernetes.registry.secret_name }}
      {% endif %}
      containers:
        - name: {{ kubernetes.deployment.container.name }}
          image: {{ image.registry }}/{{ image.name }}:{{ image.tag }}
          imagePullPolicy: Always
          ports:
            - containerPort: {{ kubernetes.deployment.container.port }}
              name: http
              protocol: TCP
          env:
            {% for key, value in kubernetes.deployment.container.environment.items() %}
            - name: {{ key }}
              value: "{{ value }}"
            {% endfor %}
          resources:
            requests:
              cpu: {{ kubernetes.deployment.container.resources.requests.cpu }}
              memory: {{ kubernetes.deployment.container.resources.requests.memory }}
            limits:
              cpu: {{ kubernetes.deployment.container.resources.limits.cpu }}
              memory: {{ kubernetes.deployment.container.resources.limits.memory }}
          {% if kubernetes.deployment.container.liveness_probe %}
          livenessProbe:
            httpGet:
              path: {{ kubernetes.deployment.container.liveness_probe.http_get.path }}
              port: {{ kubernetes.deployment.container.liveness_probe.http_get.port }}
            initialDelaySeconds: {{ kubernetes.deployment.container.liveness_probe.initial_delay_seconds }}
            periodSeconds: {{ kubernetes.deployment.container.liveness_probe.period_seconds }}
            timeoutSeconds: {{ kubernetes.deployment.container.liveness_probe.timeout_seconds }}
            failureThreshold: {{ kubernetes.deployment.container.liveness_probe.failure_threshold }}
          {% endif %}
          {% if kubernetes.deployment.container.readiness_probe %}
          readinessProbe:
            httpGet:
              path: {{ kubernetes.deployment.container.readiness_probe.http_get.path }}
              port: {{ kubernetes.deployment.container.readiness_probe.http_get.port }}
            initialDelaySeconds: {{ kubernetes.deployment.container.readiness_probe.initial_delay_seconds }}
            periodSeconds: {{ kubernetes.deployment.container.readiness_probe.period_seconds }}
            timeoutSeconds: {{ kubernetes.deployment.container.readiness_probe.timeout_seconds }}
            failureThreshold: {{ kubernetes.deployment.container.readiness_probe.failure_threshold }}
          {% endif %}
          {% if kubernetes.persistence.enabled %}
          volumeMounts:
            - name: data
              mountPath: {{ kubernetes.persistence.mount_path }}
          {% endif %}
      {% if kubernetes.persistence.enabled %}
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: {{ app.name }}-pvc
      {% endif %}
```

### service.yaml.j2

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ app.name }}
  namespace: {{ kubernetes.namespace }}
  labels:
    app: {{ app.name }}
  {% if kubernetes.service.annotations %}
  annotations:
    {% for key, value in kubernetes.service.annotations.items() %}
    {{ key }}: "{{ value }}"
    {% endfor %}
  {% endif %}
spec:
  type: {{ kubernetes.service.type }}
  ports:
    - port: {{ kubernetes.service.port }}
      targetPort: {{ kubernetes.service.target_port }}
      protocol: TCP
      name: http
  selector:
    app: {{ app.name }}
```

### configmap.yaml.j2

```yaml
{% if kubernetes.config_map.enabled %}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ app.name }}-config
  namespace: {{ kubernetes.namespace }}
  labels:
    app: {{ app.name }}
data:
  {% for key, value in kubernetes.config_map.data.items() %}
  {{ key }}: |
{{ value | indent(4) }}
  {% endfor %}
{% endif %}
```

### pvc.yaml.j2

```yaml
{% if kubernetes.persistence.enabled %}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ app.name }}-pvc
  namespace: {{ kubernetes.namespace }}
  labels:
    app: {{ app.name }}
spec:
  accessModes:
    {% for mode in kubernetes.persistence.access_modes %}
    - {{ mode }}
    {% endfor %}
  storageClassName: {{ kubernetes.persistence.storage_class }}
  resources:
    requests:
      storage: {{ kubernetes.persistence.size }}
{% endif %}
```

### ingress.yaml.j2

```yaml
{% if kubernetes.ingress.enabled %}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ app.name }}
  namespace: {{ kubernetes.namespace }}
  labels:
    app: {{ app.name }}
  {% if kubernetes.ingress.annotations %}
  annotations:
    {% for key, value in kubernetes.ingress.annotations.items() %}
    {{ key }}: "{{ value }}"
    {% endfor %}
  {% endif %}
spec:
  ingressClassName: {{ kubernetes.ingress.class_name }}
  {% if kubernetes.ingress.tls %}
  tls:
    {% for tls in kubernetes.ingress.tls %}
    - hosts:
        {% for host in tls.hosts %}
        - {{ host }}
        {% endfor %}
      secretName: {{ tls.secret_name }}
    {% endfor %}
  {% endif %}
  rules:
    {% for rule in kubernetes.ingress.rules %}
    - host: {{ rule.host }}
      http:
        paths:
          {% for path in rule.paths %}
          - path: {{ path.path }}
            pathType: {{ path.path_type }}
            backend:
              service:
                name: {{ app.name }}
                port:
                  number: {{ kubernetes.service.port }}
          {% endfor %}
    {% endfor %}
{% endif %}
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

**Objectives:**
- Configuration management system
- Updated unified Dockerfile template
- Basic CLI structure for deploy commands
- Template rendering engine

**Tasks:**
1. Create configuration schema and validation (`config.py`)
2. Update `Dockerfile.base` with Lambda Web Adapter
3. Add Jinja2 template rendering system
4. Create deploy.yaml template for `init` command
5. Update CLI with deploy command structure
6. Add configuration loader with environment variable support

**Deliverables:**
- `jvbundler/config.py` - Configuration management
- `jvbundler/templates/deploy.yaml.template` - Config template
- `jvbundler/templates/Dockerfile.unified` - Updated Dockerfile
- `jvbundler/renderer.py` - Template rendering
- Updated `cli.py` with deploy command skeleton
- Tests for configuration loading and validation
- Documentation for configuration format

**Files to Create:**
```
jvbundler/config.py
jvbundler/renderer.py
jvbundler/templates/deploy.yaml.template
jvbundler/templates/Dockerfile.unified
tests/test_config.py
tests/test_renderer.py
```

### Phase 2: Docker Build System (Week 1-2)

**Objectives:**
- Docker image building
- Multi-registry support
- Image tagging and versioning

**Tasks:**
1. Implement Docker build wrapper (`docker_builder.py`)
2. Add support for build arguments and caching
3. Implement multi-platform builds
4. Add image tagging strategy
5. Implement generic registry push (supports any registry)
6. Add build verification

**Deliverables:**
- `jvbundler/docker_builder.py` - Docker operations
- Support for Docker BuildKit
- Registry authentication handling
- Tests for Docker operations (mocked)
- Documentation for Docker build options

**Files to Create:**
```
jvbundler/docker_builder.py
tests/test_docker_builder.py
docs/DOCKER_BUILD.md
```

### Phase 3: AWS Lambda Deployment (Week 2)

**Objectives:**
- Complete end-to-end Lambda deployment
- ECR integration
- Lambda function management
- API Gateway setup

**Tasks:**
1. Implement ECR operations (`aws/ecr.py`)
   - Create/update repositories
   - Authenticate with ECR
   - Push images to ECR
   
2. Implement Lambda deployer (`aws/lambda_deployer.py`)
   - Create/update Lambda functions
   - Configure function settings
   - Update function code from ECR image
   - Configure EFS mounts
   - Configure VPC settings
   
3. Implement IAM management (`aws/iam.py`)
   - Create execution roles
   - Attach policies
   - Validate permissions
   
4. Implement API Gateway setup (`aws/api_gateway.py`)
   - Create HTTP API
   - Configure routes and integrations
   - Set up CORS
   - Configure custom domains (optional)
   - Set up throttling
   
5. Add CloudWatch Logs integration
   - Create log groups
   - Set retention policies
   - Stream logs

**Deliverables:**
- `jvbundler/aws/ecr.py` - ECR operations
- `jvbundler/aws/lambda_deployer.py` - Lambda deployment
- `jvbundler/aws/api_gateway.py` - API Gateway setup
- `jvbundler/aws/iam.py` - IAM management
- `jvbundler/aws/logs.py` - CloudWatch Logs
- Complete Lambda deployment workflow
- Tests for AWS operations (mocked with moto)
- Documentation for Lambda deployment

**Files to Create:**
```
jvbundler/aws/__init__.py
jvbundler/aws/ecr.py
jvbundler/aws/lambda_deployer.py
jvbundler/aws/api_gateway.py
jvbundler/aws/iam.py
jvbundler/aws/logs.py
tests/aws/__init__.py
tests/aws/test_ecr.py
tests/aws/test_lambda_deployer.py
tests/aws/test_api_gateway.py
tests/aws/test_iam.py
docs/LAMBDA_DEPLOYMENT.md
```

### Phase 4: Kubernetes Deployment (Week 3)

**Objectives:**
- Kubernetes manifest generation
- kubectl integration
- End-to-end K8s deployment

**Tasks:**
1. Create Kubernetes manifest templates (Jinja2)
   - Deployment template
   - Service template
   - ConfigMap template
   - PVC template
   - Ingress template
   
2. Implement manifest generator (`k8s/manifests.py`)
   - Render templates with configuration
   - Validate manifests
   - Support multiple manifest types
   
3. Implement kubectl wrapper (`k8s/kubectl.py`)
   - Execute kubectl commands
   - Handle context switching
   - Stream output
   
4. Implement Kubernetes deployer (`k8s/k8s_deployer.py`)
   - Apply manifests
   - Wait for rollout completion
   - Handle rollback on failure
   - Validate deployment health
   
5. Add Docker registry support
   - Support any Docker registry
   - Create image pull secrets
   - Handle authentication

**Deliverables:**
- `jvbundler/k8s/templates/*.j2` - Manifest templates
- `jvbundler/k8s/manifests.py` - Manifest generation
- `jvbundler/k8s/kubectl.py` - kubectl wrapper
- `jvbundler/k8s/k8s_deployer.py` - K8s deployment
- Complete K8s deployment workflow
- Tests for K8s operations (mocked)
- Documentation for K8s deployment

**Files to Create:**
```
jvbundler/k8s/__init__.py
jvbundler/k8s/manifests.py
jvbundler/k8s/kubectl.py
jvbundler/k8s/k8s_deployer.py
jvbundler/k8s/templates/deployment.yaml.j2
jvbundler/k8s/templates/service.yaml.j2
jvbundler/k8s/templates/configmap.yaml.j2
jvbundler/k8s/templates/pvc.yaml.j2
jvbundler/k8s/templates/ingress.yaml.j2
tests/k8s/__init__.py
tests/k8s/test_manifests.py
tests/k8s/test_kubectl.py
tests/k8s/test_k8s_deployer.py
docs/K8S_DEPLOYMENT.md
```

### Phase 5: Status and Monitoring (Week 3-4)

**Objectives:**
- Deployment status checking
- Log viewing and streaming
- Health monitoring

**Tasks:**
1. Implement Lambda status checker
   - Get function status
   - Check API Gateway status
   - Show configuration
   - Validate deployment health
   
2. Implement K8s status checker
   - Get deployment status
   - List pods
   - Show service endpoints
   - Check health status
   
3. Implement log viewing
   - Lambda CloudWatch Logs streaming
   - K8s pod log streaming
   - Log filtering and formatting
   
4. Add deployment verification
   - Test endpoints
   - Verify health checks
   - Check resource utilization

**Deliverables:**
- `jvbundler/status.py` - Status checking
- `jvbundler/logs.py` - Log viewing
- Enhanced CLI with status/logs commands
- Tests for status/logs functionality
- Documentation

**Files to Create:**
```
jvbundler/status.py
jvbundler/logs.py
tests/test_status.py
tests/test_logs.py
docs/MONITORING.md
```

### Phase 6: Polish and Documentation (Week 4)

**Objectives:**
- Complete documentation
- Examples and tutorials
- CI/CD integration guides
- Error handling improvements

**Tasks:**
1. Write comprehensive documentation
   - Getting started guide
   - Configuration reference
   - Lambda deployment guide
   - K8s deployment guide
   - Troubleshooting guide
   
2. Create example configurations
   - Simple app examples
   - Production-ready examples
   - Multi-environment setups
   
3. Create CI/CD examples
   - GitHub Actions workflows
   - GitLab CI pipelines
   - Jenkins pipelines
   
4. Improve error handling
   - Better error messages
   - Validation feedback
   - Rollback mechanisms
   
5. Add dry-run support
   - Show what will be done
   - Validate configuration
   - Preview generated resources

**Deliverables:**
- Complete documentation suite
- Example configurations
- CI/CD examples
- Improved error handling
- Dry-run functionality

**Files to Create:**
```
docs/GETTING_STARTED.md
docs/CONFIGURATION_REFERENCE.md
docs/TROUBLESHOOTING.md
examples/simple-app/
examples/production-app/
examples/ci-cd/github-actions.yml
examples/ci-cd/gitlab-ci.yml
examples/ci-cd/Jenkinsfile
```

## File Structure (Complete)

```
jvbundler/
├── jvbundler/
│   ├── __init__.py                 # Package init
│   ├── bundler.py                  # Existing bundler
│   ├── cli.py                      # Enhanced CLI
│   ├── dockerfile_generator.py     # Existing generator
│   ├── config.py                   # NEW: Config management
│   ├── docker_builder.py           # NEW: Docker operations
│   ├── renderer.py                 # NEW: Template rendering
│   ├── status.py                   # NEW: Status checking
│   ├── logs.py                     # NEW: Log viewing
│   │
│   ├── aws/                        # NEW: AWS-specific
│   │   ├── __init__.py