# jvbundler Deployment - Quick Reference Guide

## Installation

```bash
pip install jvbundler
```

## Quick Start

### 1. Initialize Deployment Configuration

```bash
cd my-jvagent-app
jvbundler init --all
```

This creates `deploy.yaml` with both Lambda and Kubernetes configurations.

### 2. Configure deploy.yaml

Edit `deploy.yaml` with your settings:

```yaml
app:
  name: my-app
  version: "1.0.0"

lambda:
  enabled: true
  region: us-east-1
  function:
    memory: 1024
    timeout: 300

kubernetes:
  enabled: true
  namespace: default
  deployment:
    replicas: 2
```

### 3. Deploy

```bash
# Lambda (complete end-to-end)
jvbundler deploy lambda --all

# Kubernetes (complete end-to-end)
jvbundler deploy k8s --all
```

## Command Reference

### Bundle (Existing)

```bash
# Generate Dockerfile
jvbundler                    # Current directory
jvbundler /path/to/app      # Specific path
jvbundler --debug           # Debug mode
```

### Initialize

```bash
jvbundler init              # Create deploy.yaml (both platforms)
jvbundler init --lambda     # Lambda only
jvbundler init --kubernetes # Kubernetes only
```

### Deploy to Lambda

```bash
# Complete deployment (build + push + update + api)
jvbundler deploy lambda --all

# Individual steps
jvbundler deploy lambda --build        # Build Docker image
jvbundler deploy lambda --push         # Push to ECR
jvbundler deploy lambda --update       # Update Lambda function
jvbundler deploy lambda --create-api   # Create/update API Gateway

# With options
jvbundler deploy lambda --all \
  --region us-west-2 \
  --function my-app-prod \
  --env LOG_LEVEL=DEBUG

# Dry run (show what would happen)
jvbundler deploy lambda --all --dry-run
```

### Deploy to Kubernetes

```bash
# Complete deployment (build + push + apply)
jvbundler deploy k8s --all

# Individual steps
jvbundler deploy k8s --build          # Build Docker image
jvbundler deploy k8s --push           # Push to registry
jvbundler deploy k8s --apply          # Apply manifests

# With options
jvbundler deploy k8s --all \
  --namespace production \
  --context prod-cluster \
  --env LOG_LEVEL=DEBUG

# Dry run (show manifests)
jvbundler deploy k8s --all --dry-run
```

### Status

```bash
# Lambda status
jvbundler status lambda
jvbundler status lambda --function my-app --region us-east-1
jvbundler status lambda --json  # JSON output

# Kubernetes status
jvbundler status k8s
jvbundler status k8s --namespace production
jvbundler status k8s --json  # JSON output
```

### Logs

```bash
# Lambda logs
jvbundler logs lambda --follow         # Stream logs
jvbundler logs lambda --tail 100       # Last 100 lines
jvbundler logs lambda --since 1h       # Last hour

# Kubernetes logs
jvbundler logs k8s --follow            # Stream logs
jvbundler logs k8s --pod my-app-abc    # Specific pod
jvbundler logs k8s --tail 100          # Last 100 lines
```

### Destroy

```bash
# Lambda
jvbundler destroy lambda --yes                    # Delete function
jvbundler destroy lambda --delete-api --yes       # Delete API too
jvbundler destroy lambda --delete-role --yes      # Delete IAM role too

# Kubernetes
jvbundler destroy k8s --yes                       # Delete all resources
jvbundler destroy k8s --namespace production --yes
```

## Configuration Reference

### Minimal deploy.yaml

```yaml
version: "1.0"

app:
  name: my-app
  version: "1.0.0"

lambda:
  enabled: true
  region: us-east-1

kubernetes:
  enabled: true
  namespace: default
```

### Common Configuration Options

#### Lambda Configuration

```yaml
lambda:
  enabled: true
  region: us-east-1
  
  function:
    name: my-app
    memory: 1024          # MB (128-10240)
    timeout: 300          # seconds (1-900)
    architecture: x86_64  # x86_64 or arm64
  
  environment:
    JVAGENT_ADMIN_PASSWORD: "${JVAGENT_ADMIN_PASSWORD}"
    LOG_LEVEL: "INFO"
  
  efs:
    enabled: true
    file_system_id: "fs-1234567890abcdef0"
    access_point_arn: "arn:aws:elasticfilesystem:..."
    mount_path: "/mnt/efs"
  
  api_gateway:
    enabled: true
    type: "HTTP"
    stage_name: "prod"
    cors:
      enabled: true
```

#### Kubernetes Configuration

```yaml
kubernetes:
  enabled: true
  namespace: default
  context: my-cluster
  
  deployment:
    replicas: 2
    
    container:
      port: 8080
      
      environment:
        JVAGENT_ADMIN_PASSWORD: "${JVAGENT_ADMIN_PASSWORD}"
        LOG_LEVEL: "INFO"
      
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "1000m"
          memory: "1Gi"
      
      liveness_probe:
        http_get:
          path: "/health"
          port: 8080
        initial_delay_seconds: 30
  
  service:
    type: "LoadBalancer"
    port: 80
    target_port: 8080
  
  persistence:
    enabled: true
    storage_class: "gp2"
    size: "10Gi"
    mount_path: "/data"
```

## Environment Variables

Required environment variables should be set before deployment:

```bash
# Required
export JVAGENT_ADMIN_PASSWORD=your-secure-password

# AWS (if not using IAM roles)
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1

# Kubernetes (if not using default kubeconfig)
export KUBECONFIG=/path/to/kubeconfig
```

## Unified Dockerfile

The same Dockerfile works for both Lambda and Kubernetes:

```dockerfile
FROM python:3.12-slim

# Lambda Web Adapter (enables Lambda compatibility)
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 \
     /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /var/task
COPY . .
RUN pip install -r requirements.txt

# Action dependencies (auto-generated)
# {{ACTION_DEPENDENCIES}}

EXPOSE 8080

# Lambda Web Adapter config
ENV PORT=8080
ENV AWS_LWA_READINESS_CHECK_PATH=/health

# Health check
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1

# Start HTTP server (works in both Lambda and K8s)
CMD ["python", "-m", "uvicorn", "jvagent.server:app", \
     "--host", "0.0.0.0", "--port", "8080"]
```

## Common Workflows

### Deploy to Both Platforms

```bash
# 1. Initialize
jvbundler init --all

# 2. Edit deploy.yaml

# 3. Deploy to Lambda
jvbundler deploy lambda --all

# 4. Deploy to K8s (reuses same image)
jvbundler deploy k8s --push --apply

# 5. Check status
jvbundler status lambda
jvbundler status k8s
```

### Update Existing Deployment

```bash
# Update Lambda function only (no rebuild)
jvbundler deploy lambda --update

# Update K8s deployment only (no rebuild)
jvbundler deploy k8s --apply

# Full rebuild and update
jvbundler deploy lambda --all
jvbundler deploy k8s --all
```

### Multi-Environment Deployment

```bash
# Development
jvbundler deploy lambda --all \
  --config deploy.dev.yaml \
  --function my-app-dev \
  --region us-east-1

# Production
jvbundler deploy lambda --all \
  --config deploy.prod.yaml \
  --function my-app-prod \
  --region us-west-2
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Lambda
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          JVAGENT_ADMIN_PASSWORD: ${{ secrets.ADMIN_PASSWORD }}
        run: |
          pip install jvbundler
          jvbundler deploy lambda --all
```

#### GitLab CI

```yaml
deploy:
  image: python:3.12
  script:
    - pip install jvbundler
    - jvbundler deploy lambda --all
  only:
    - main
```

## Troubleshooting

### Lambda Deployment Issues

```bash
# Check function status
jvbundler status lambda --function my-app

# View recent logs
jvbundler logs lambda --tail 100

# Test with dry-run
jvbundler deploy lambda --all --dry-run

# Verify IAM permissions
aws sts get-caller-identity

# Check ECR repository
aws ecr describe-repositories --region us-east-1
```

### Kubernetes Deployment Issues

```bash
# Check deployment status
jvbundler status k8s

# View pod logs
jvbundler logs k8s --follow

# Check with kubectl directly
kubectl get pods -n default
kubectl describe deployment my-app
kubectl logs -f deployment/my-app

# Verify kubectl context
kubectl config current-context
kubectl cluster-info
```

### Common Errors

**"app.yaml not found"**
- Ensure you're in the jvagent app root directory
- Or specify the path: `jvbundler /path/to/app`

**"deploy.yaml not found"**
- Run `jvbundler init --all` first
- Or specify config: `--config deploy.yaml`

**"Docker build failed"**
- Check Dockerfile.base exists
- Verify requirements.txt is valid
- Check disk space: `df -h`

**"ECR authentication failed"**
- Verify AWS credentials: `aws sts get-caller-identity`
- Check region: `--region us-east-1`
- Ensure ECR permissions in IAM policy

**"kubectl not found"**
- Install kubectl: `brew install kubectl` (macOS)
- Or use official installation guide

**"Permission denied"**
- Lambda: Check IAM policy includes Lambda/ECR/API Gateway permissions
- K8s: Check RBAC permissions in cluster

## Best Practices

### Security

1. **Never commit credentials** to version control
2. **Use environment variables** for secrets
3. **Enable IAM roles** instead of access keys when possible
4. **Use Kubernetes ServiceAccounts** for pod authentication
5. **Rotate credentials** regularly

### Configuration

1. **Use separate configs** for dev/staging/prod
2. **Version your deploy.yaml** with your code
3. **Document environment-specific** settings
4. **Use template variables** for reusability
5. **Validate configs** with dry-run before deploying

### Deployment

1. **Test in development** first
2. **Use dry-run** to preview changes
3. **Monitor logs** during deployment
4. **Verify health checks** after deployment
5. **Keep rollback plan** ready

### Monitoring

1. **Check status** after deployment
2. **Monitor logs** for errors
3. **Set up CloudWatch alarms** (Lambda)
4. **Use Prometheus/Grafana** (Kubernetes)
5. **Test endpoints** after deployment

## Resources

- [Full Deployment Specification](DEPLOYMENT_SPEC.md)
- [Implementation Plan](IMPLEMENTATION_PLAN.md)
- [Lambda Deployment Guide](docs/LAMBDA_DEPLOYMENT.md)
- [Kubernetes Deployment Guide](docs/K8S_DEPLOYMENT.md)
- [Configuration Reference](docs/CONFIGURATION_REFERENCE.md)

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/jvbundler/issues
- Documentation: See `docs/` directory
- Examples: See `examples/` directory

## Version

This quick reference is for jvbundler v0.2.0 (deployment features).