# jvbundler Deployment - Quick Start Guide

Get your jvagent application deployed to AWS Lambda in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Docker installed and running
- AWS account with credentials configured
- jvagent application ready to deploy

## Step 1: Install jvbundler with Deployment Features

```bash
pip install jvbundler[deploy]
```

Or if you have the source:

```bash
cd jvbundler
pip install -e ".[deploy]"
```

## Step 2: Configure AWS Credentials

Choose one method:

### Option A: AWS CLI
```bash
aws configure
```

### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Option C: AWS Profile
```bash
export AWS_PROFILE="your-profile-name"
```

## Step 3: Initialize Deployment Configuration

Navigate to your jvagent application directory:

```bash
cd my-jvagent-app
jvbundler init --lambda
```

This creates a `deploy.yaml` file with sensible defaults.

## Step 4: Configure Your Deployment

Edit the `deploy.yaml` file that was just created:

```bash
vim deploy.yaml
```

**Minimum required changes:**

1. Set your AWS account ID:
```yaml
lambda:
  account_id: "123456789012"  # Your 12-digit AWS account ID
```

2. Customize your app name (optional):
```yaml
app:
  name: my-jvagent-app  # Change this to your app name
```

## Step 5: Set Required Environment Variables

```bash
export JVAGENT_ADMIN_PASSWORD="your-secure-password-here"
```

## Step 6: Test with Dry Run

Before deploying, do a dry run to see what will happen:

```bash
jvbundler deploy lambda --all --dry-run
```

You should see output like:
```
🔍 DRY RUN MODE - No changes will be made

📦 Deploying to AWS Lambda
   Region: us-east-1
   Function: my-jvagent-app
   Image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-jvagent-app:1.0.0

[DRY RUN] Would ensure ECR repository: my-jvagent-app
[DRY RUN] Would build and push image: ...
[DRY RUN] Would ensure IAM role: my-jvagent-app-lambda-role
[DRY RUN] Would deploy Lambda function: my-jvagent-app
[DRY RUN] Would create HTTP API: my-jvagent-app-api

✓ Lambda deployment completed successfully!
```

## Step 7: Deploy!

If the dry run looks good, deploy for real:

```bash
jvbundler deploy lambda --all
```

This will:
1. ✅ Create an ECR repository (if needed)
2. ✅ Build your Docker image (Note: Currently you need to build/push manually)
3. ✅ Create an IAM role with necessary permissions
4. ✅ Deploy your Lambda function
5. ✅ Create an API Gateway endpoint

## Step 8: Get Your API URL

After deployment completes, you'll see:

```
✓ Lambda deployment completed successfully!
  Function ARN: arn:aws:lambda:us-east-1:123456789012:function:my-jvagent-app
  API URL: https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
```

**Your API is now live at that URL!** 🎉

## Step 9: Test Your Deployment

### Check Status
```bash
jvbundler status lambda
```

Output:
```
📊 Lambda Function Status
   Function: my-jvagent-app
   State: Active
   ARN: arn:aws:lambda:us-east-1:123456789012:function:my-jvagent-app
   Memory: 1024 MB
   Timeout: 300 seconds
```

### View Logs
```bash
jvbundler logs lambda --since 5m
```

### Stream Logs in Real-Time
```bash
jvbundler logs lambda --follow
```

## Common Issues and Solutions

### Issue: "Configuration file not found"
**Solution:** Run `jvbundler init --lambda` first

### Issue: "boto3 is required"
**Solution:** Install with deployment features: `pip install jvbundler[deploy]`

### Issue: "Lambda account_id is required"
**Solution:** Add your AWS account ID to `deploy.yaml`:
```yaml
lambda:
  account_id: "123456789012"
```

Find your account ID with: `aws sts get-caller-identity`

### Issue: "Environment variable 'JVAGENT_ADMIN_PASSWORD' not found"
**Solution:** Set the environment variable:
```bash
export JVAGENT_ADMIN_PASSWORD="your-password"
```

### Issue: Docker build errors
**Solution:** Ensure Docker is installed and running:
```bash
docker version
```

## Next Steps

### Update Your Deployment
When you make changes to your code:

```bash
# Rebuild and redeploy
jvbundler deploy lambda --all
```

### Deploy to Different Regions
```bash
jvbundler deploy lambda --all --region us-west-2
```

### Deploy with Different Settings
```bash
jvbundler deploy lambda --all \
  --function my-app-staging \
  --env LOG_LEVEL=DEBUG \
  --env FEATURE_FLAG=true
```

### Destroy When Done
To clean up and delete all resources:

```bash
jvbundler destroy lambda --yes --delete-api --delete-role
```

## Complete Example Workflow

Here's a complete example from start to finish:

```bash
# 1. Navigate to your app
cd my-jvagent-app

# 2. Initialize deployment config
jvbundler init --lambda

# 3. Edit config (set account_id)
vim deploy.yaml

# 4. Set environment variables
export JVAGENT_ADMIN_PASSWORD="secure-password-123"
export AWS_PROFILE="my-aws-profile"

# 5. Test with dry run
jvbundler deploy lambda --all --dry-run

# 6. Deploy for real
jvbundler deploy lambda --all

# 7. Check status
jvbundler status lambda

# 8. View logs
jvbundler logs lambda --follow

# 9. Test your API
curl https://your-api-url.execute-api.us-east-1.amazonaws.com/prod/health

# 10. When done, clean up
jvbundler destroy lambda --yes
```

## Configuration Template

Minimal `deploy.yaml`:

```yaml
version: "1.0"

app:
  name: my-app
  version: "1.0.0"

image:
  name: my-app
  tag: "1.0.0"

lambda:
  enabled: true
  region: us-east-1
  account_id: "123456789012"
  
  function:
    name: my-app
    memory: 1024
    timeout: 300
  
  ecr:
    repository_name: my-app
    create_if_missing: true
  
  environment:
    JVAGENT_ADMIN_PASSWORD: "${JVAGENT_ADMIN_PASSWORD}"
    LOG_LEVEL: "INFO"
  
  iam:
    role_name: my-app-lambda-role
    policies:
      - "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  
  api_gateway:
    enabled: true
    type: "HTTP"
    cors:
      enabled: true
```

## Tips and Best Practices

### 1. Use Environment Variables for Secrets
Never hardcode passwords in `deploy.yaml`. Use `${ENV_VAR}` syntax:
```yaml
environment:
  API_KEY: "${MY_API_KEY}"
```

### 2. Test with Dry Run First
Always run with `--dry-run` before actual deployment:
```bash
jvbundler deploy lambda --all --dry-run
```

### 3. Use Different Configs for Different Environments
```bash
jvbundler init --lambda --config deploy.dev.yaml
jvbundler init --lambda --config deploy.prod.yaml
```

### 4. Set Appropriate Memory and Timeout
Adjust based on your app's needs:
```yaml
function:
  memory: 2048  # More memory = more CPU
  timeout: 900  # Max is 900 seconds (15 minutes)
```

### 5. Monitor Your Logs
Stream logs during deployment to catch issues early:
```bash
jvbundler logs lambda --follow
```

## Getting Help

- **Full Documentation**: See `DEPLOY_README.md`
- **Implementation Details**: See `DEPLOY_IMPLEMENTATION.md`
- **All Commands**: Run `jvbundler --help`
- **Command Help**: Run `jvbundler deploy lambda --help`

## What's Next?

- ✅ **Lambda Deployment**: Fully functional
- 🚧 **Docker Build Integration**: Coming soon
- 🚧 **Kubernetes Deployment**: In development

## Troubleshooting

If you run into issues:

1. Check the logs: `jvbundler logs lambda`
2. Verify your config: `cat deploy.yaml`
3. Check AWS credentials: `aws sts get-caller-identity`
4. Try with debug logging: `jvbundler --debug deploy lambda --all`

## Success Checklist

- [ ] jvbundler installed with deploy features
- [ ] AWS credentials configured
- [ ] deploy.yaml created and configured
- [ ] JVAGENT_ADMIN_PASSWORD environment variable set
- [ ] Dry run completed successfully
- [ ] Deployment completed successfully
- [ ] API URL received and tested
- [ ] Logs visible and showing expected output

**Congratulations! Your jvagent application is now running on AWS Lambda!** 🚀

For more advanced features and configuration options, see the full [DEPLOY_README.md](DEPLOY_README.md).