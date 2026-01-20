# jvbundler Deployment Guide

This guide explains how to use jvbundler's deployment features to deploy jvagent applications to AWS Lambda and Kubernetes.

## Overview

jvbundler now supports end-to-end deployment of jvagent applications to:
- **AWS Lambda** - Serverless deployment with API Gateway
- **Kubernetes** - Container orchestration (coming soon)

## Installation

Install jvbundler with deployment features:

```bash
pip install jvbundler[deploy]
```

Or for development:

```bash
pip install -e ".[deploy]"
```

## Quick Start

### 1. Initialize Deployment Configuration

Create a `deploy.yaml` configuration file:

```bash
cd my-jvagent-app
jvbundler init --all
```

This creates a `deploy.yaml` file with configuration for both Lambda and Kubernetes.

### 2. Configure Your Deployment

Edit `deploy.yaml` to customize your deployment:

```yaml
version: "1.0"

app:
  name: my-jvagent-app
  version: "1.0.0"

lambda:
  enabled: true
  region: us-east-1
  function:
    name: my-jvagent-app
    memory: 1024
    timeout: 300
  environment:
    JVAGENT_ADMIN_PASSWORD: "${JVAGENT_ADMIN_PASSWORD}"
```

### 3. Set Required Environment Variables

```bash
export JVAGENT_ADMIN_PASSWORD="your-secure-password"
export AWS_PROFILE="your-aws-profile"  # or use AWS credentials
```

### 4. Deploy to AWS Lambda

Deploy your application with a single command:

```bash
jvbundler deploy lambda --all
```

This will:
1. Create an ECR repository (if it doesn't exist)
2. Build and push your Docker image to ECR
3. Create an IAM role (if needed)
4. Create or update the Lambda function
5. Create an API Gateway endpoint

## Commands

### `jvbundler init`

Initialize deployment configuration.

```bash
# Create deploy.yaml with both Lambda and Kubernetes config
jvbundler init --all

# Create with only Lambda configuration
jvbundler init --lambda

# Create with only Kubernetes configuration
jvbundler init --kubernetes

# Specify custom config file name
jvbundler init --config my-deploy.yaml
```

### `jvbundler deploy lambda`

Deploy to AWS Lambda.

```bash
# Full deployment (all steps)
jvbundler deploy lambda --all

# Deploy with overrides
jvbundler deploy lambda --all --region us-west-2 --function my-app-prod

# Override environment variables
jvbundler deploy lambda --all --env LOG_LEVEL=DEBUG

# Dry run (see what would happen)
jvbundler deploy lambda --all --dry-run

# Update only the Lambda function (no rebuild)
jvbundler deploy lambda --update

# Create/update only the API Gateway
jvbundler deploy lambda --create-api
```

### `jvbundler status lambda`

Check Lambda deployment status.

```bash
# Check status using deploy.yaml
jvbundler status lambda

# Check specific function
jvbundler status lambda --function my-app --region us-east-1

# Get status as JSON
jvbundler status lambda --json
```

### `jvbundler logs lambda`

View Lambda function logs.

```bash
# View recent logs
jvbundler logs lambda

# Stream logs in real-time
jvbundler logs lambda --follow

# Show last 50 lines
jvbundler logs lambda --tail 50

# Show logs from last 5 minutes
jvbundler logs lambda --since 5m

# Show logs from last 2 hours
jvbundler logs lambda --since 2h

# Specific function
jvbundler logs lambda --function my-app --region us-east-1
```

### `jvbundler destroy lambda`

Destroy Lambda deployment.

```bash
# Destroy Lambda function (with confirmation)
jvbundler destroy lambda

# Destroy Lambda function without confirmation
jvbundler destroy lambda --yes

# Also delete API Gateway
jvbundler destroy lambda --yes --delete-api

# Also delete IAM role
jvbundler destroy lambda --yes --delete-role

# Delete everything
jvbundler destroy lambda --yes --delete-api --delete-role
```

## Configuration Reference

### Lambda Configuration

Key configuration options in `deploy.yaml`:

```yaml
lambda:
  enabled: true
  region: us-east-1
  account_id: "123456789012"  # Optional, auto-detected
  
  function:
    name: my-jvagent-app
    description: "My jvagent application"
    memory: 1024              # MB (128-10240)
    timeout: 300              # seconds (1-900)
    architecture: x86_64      # x86_64 or arm64
    ephemeral_storage: 512    # MB (512-10240)
  
  ecr:
    repository_name: my-jvagent-app
    create_if_missing: true
  
  environment:
    JVAGENT_ADMIN_PASSWORD: "${JVAGENT_ADMIN_PASSWORD}"
    JVSPATIAL_DB_TYPE: "json"
    LOG_LEVEL: "INFO"
  
  iam:
    role_arn: null            # null = auto-create
    role_name: my-app-lambda-role
    policies:
      - "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  
  vpc:
    enabled: false
    security_group_ids: []
    subnet_ids: []
  
  efs:
    enabled: false
    file_system_id: ""
    access_point_arn: ""
    mount_path: "/mnt/efs"
  
  api_gateway:
    enabled: true
    type: "HTTP"              # HTTP or REST
    name: my-app-api
    stage_name: "prod"
    cors:
      enabled: true
      allow_origins: ["*"]
      allow_methods: ["*"]
      allow_headers: ["*"]
```

## Environment Variable Interpolation

Use `${VAR_NAME}` syntax to reference environment variables:

```yaml
environment:
  JVAGENT_ADMIN_PASSWORD: "${JVAGENT_ADMIN_PASSWORD}"
  API_KEY: "${MY_API_KEY}"
```

## Template Variables

Use `{{variable}}` syntax for internal references:

```yaml
app:
  name: my-app
  version: "1.0.0"

image:
  name: my-app
  tag: "{{app.version}}"  # References app.version

lambda:
  function:
    name: "{{app.name}}"    # References app.name
```

## AWS Prerequisites

Before deploying to Lambda, ensure you have:

1. **AWS Credentials**: Configure AWS credentials using:
   - AWS CLI: `aws configure`
   - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - AWS Profile: `AWS_PROFILE=myprofile`

2. **Required IAM Permissions**:
   - ECR: Create repositories, push images
   - Lambda: Create/update functions
   - IAM: Create roles and attach policies (if auto-creating roles)
   - API Gateway: Create/update HTTP APIs
   - CloudWatch Logs: Read log streams (for logs command)

3. **Docker**: Docker must be installed and running for image builds

## Example Workflows

### Simple Development Deployment

```bash
# Initialize
cd my-jvagent-app
jvbundler init --lambda

# Edit deploy.yaml as needed
vim deploy.yaml

# Set environment variables
export JVAGENT_ADMIN_PASSWORD="dev-password"

# Deploy
jvbundler deploy lambda --all

# View logs
jvbundler logs lambda --follow
```

### Production Deployment

```bash
# Use separate config for production
jvbundler init --lambda --config deploy.prod.yaml

# Edit production config
vim deploy.prod.yaml

# Deploy with production settings
jvbundler deploy lambda --all --config deploy.prod.yaml --env LOG_LEVEL=WARNING

# Check status
jvbundler status lambda --config deploy.prod.yaml

# Monitor logs
jvbundler logs lambda --config deploy.prod.yaml --follow
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy to Lambda
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install jvbundler
        run: pip install jvbundler[deploy]
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to Lambda
        env:
          JVAGENT_ADMIN_PASSWORD: ${{ secrets.JVAGENT_ADMIN_PASSWORD }}
        run: |
          cd my-jvagent-app
          jvbundler deploy lambda --all
```

## Troubleshooting

### "Configuration file not found"

Make sure you've run `jvbundler init` first:

```bash
jvbundler init --all
```

### "boto3 is required"

Install deployment dependencies:

```bash
pip install jvbundler[deploy]
# or
pip install boto3
```

### "Lambda deployment is not enabled"

Edit `deploy.yaml` and set:

```yaml
lambda:
  enabled: true
```

### "ECR repository does not exist"

Set `create_if_missing: true` in `deploy.yaml`:

```yaml
lambda:
  ecr:
    create_if_missing: true
```

### Docker build issues

Ensure Docker is installed and running:

```bash
docker version
```

### AWS permissions errors

Ensure your AWS credentials have the required permissions (see AWS Prerequisites above).

### Function invocation errors

Check logs for details:

```bash
jvbundler logs lambda --since 10m
```

## Next Steps

- **Read the full specification**: See `DEPLOYMENT_SPEC.md` for complete technical details
- **Review implementation plan**: See `IMPLEMENTATION_PLAN.md` for development roadmap
- **Check quick reference**: See `DEPLOYMENT_QUICKREF.md` for command cheat sheet
- **Kubernetes deployment**: Coming soon - use `jvbundler deploy k8s`

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/jvbundler/issues
- Documentation: See `docs/` directory
- Examples: See `examples/` directory

## Status

✅ **AWS Lambda deployment** - Fully implemented
🚧 **Kubernetes deployment** - Coming soon
🚧 **Docker build system** - Coming soon
🚧 **Log streaming** - Partially implemented

## License

MIT License - See LICENSE file for details