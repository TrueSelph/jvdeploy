# jvbundler Deployment - Implementation Plan

## Overview

This document outlines the detailed implementation plan for adding AWS Lambda and Kubernetes deployment capabilities to jvbundler. The implementation is divided into 6 phases over 4 weeks.

## Timeline Summary

- **Phase 1**: Core Infrastructure (Week 1, Days 1-3)
- **Phase 2**: Docker Build System (Week 1-2, Days 3-6)
- **Phase 3**: AWS Lambda Deployment (Week 2, Days 7-10)
- **Phase 4**: Kubernetes Deployment (Week 3, Days 11-15)
- **Phase 5**: Status and Monitoring (Week 3-4, Days 15-18)
- **Phase 6**: Polish and Documentation (Week 4, Days 19-20)

---

## Phase 1: Core Infrastructure (Days 1-3)

### Goal
Establish the foundation for deployment features: configuration management, template rendering, and CLI structure.

### Tasks

#### Task 1.1: Configuration Management (Day 1, 4 hours)
**File**: `jvbundler/config.py`

**Requirements:**
- Load and parse `deploy.yaml` configuration file
- Validate configuration against schema
- Support environment variable interpolation (`${VAR_NAME}`)
- Support template variables (`{{app.name}}`)
- Provide sensible defaults
- Handle missing or invalid configuration gracefully

**Implementation Details:**
```python
class DeployConfig:
    """Manage deployment configuration."""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate()
        self._interpolate_env_vars()
        self._resolve_templates()
    
    def _load_config(self) -> dict:
        """Load YAML configuration."""
        pass
    
    def _validate(self):
        """Validate configuration structure."""
        pass
    
    def _interpolate_env_vars(self):
        """Replace ${VAR} with environment variables."""
        pass
    
    def _resolve_templates(self):
        """Resolve {{var}} template variables."""
        pass
    
    def get_lambda_config(self) -> dict:
        """Get Lambda-specific configuration."""
        pass
    
    def get_k8s_config(self) -> dict:
        """Get Kubernetes-specific configuration."""
        pass
```

**Tests:**
- Load valid configuration
- Handle missing file
- Validate required fields
- Environment variable interpolation
- Template variable resolution
- Invalid configuration handling

**Acceptance Criteria:**
- [ ] Can load deploy.yaml file
- [ ] Validates all required fields
- [ ] Substitutes environment variables
- [ ] Resolves template variables
- [ ] Provides helpful error messages
- [ ] All tests passing

---

#### Task 1.2: Template Rendering (Day 1, 3 hours)
**File**: `jvbundler/renderer.py`

**Requirements:**
- Render Jinja2 templates with configuration data
- Support filters and custom functions
- Handle template errors gracefully
- Validate rendered output

**Implementation Details:**
```python
class TemplateRenderer:
    """Render Jinja2 templates."""
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.env = self._setup_jinja_env()
    
    def _setup_jinja_env(self) -> Environment:
        """Configure Jinja2 environment."""
        pass
    
    def render(self, template_name: str, context: dict) -> str:
        """Render a template with context."""
        pass
    
    def render_string(self, template_str: str, context: dict) -> str:
        """Render a template string."""
        pass
```

**Tests:**
- Render simple template
- Template with variables
- Template with loops
- Template with conditionals
- Handle missing template
- Handle rendering errors

**Acceptance Criteria:**
- [ ] Can render Jinja2 templates
- [ ] Handles template errors gracefully
- [ ] Supports custom filters
- [ ] All tests passing

---

#### Task 1.3: Deploy Configuration Template (Day 1, 2 hours)
**File**: `jvbundler/templates/deploy.yaml.template`

**Requirements:**
- Complete deploy.yaml template with all options
- Comprehensive comments explaining each option
- Sensible defaults
- Examples for common scenarios

**Acceptance Criteria:**
- [ ] Template includes all configuration options
- [ ] Well-documented with comments
- [ ] Can be customized for different use cases
- [ ] Validated by config loader

---

#### Task 1.4: Updated Unified Dockerfile (Day 2, 3 hours)
**File**: `jvbundler/templates/Dockerfile.unified`

**Requirements:**
- Works in both Lambda and Kubernetes
- Uses AWS Lambda Web Adapter
- Includes health check endpoints
- Optimized for layer caching
- Supports multi-platform builds

**Implementation:**
```dockerfile
FROM python:3.12-slim

# Lambda Web Adapter for Lambda compatibility
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 \
     /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /var/task

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /var/task/

# {{ACTION_DEPENDENCIES}}

# Expose HTTP port
EXPOSE 8080

# Lambda Web Adapter configuration
ENV PORT=8080
ENV AWS_LWA_INVOKE_MODE=response_stream
ENV AWS_LWA_READINESS_CHECK_PATH=/health

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8080/health || exit 1

# Start HTTP server
CMD ["python", "-m", "uvicorn", "jvagent.server:app", \
     "--host", "0.0.0.0", "--port", "8080"]
```

**Tests:**
- Build Dockerfile successfully
- Health check endpoint works
- Can run in Docker locally
- Environment variables configured correctly

**Acceptance Criteria:**
- [ ] Dockerfile builds successfully
- [ ] Works in Lambda environment
- [ ] Works in Kubernetes environment
- [ ] Health checks functional
- [ ] Optimized layer caching

---

#### Task 1.5: CLI Structure Enhancement (Day 2-3, 4 hours)
**File**: `jvbundler/cli.py` (enhanced)

**Requirements:**
- Add `init` command
- Add `deploy` command group
- Add `status` command group
- Add `logs` command group
- Add `destroy` command group
- Maintain backward compatibility

**Implementation:**
```python
def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    
    if not args or args[0] == "bundle":
        handle_bundle_command(args)
    elif args[0] == "init":
        handle_init_command(args)
    elif args[0] == "deploy":
        handle_deploy_command(args)
    elif args[0] == "status":
        handle_status_command(args)
    elif args[0] == "logs":
        handle_logs_command(args)
    elif args[0] == "destroy":
        handle_destroy_command(args)
    else:
        print_usage()

def handle_init_command(args):
    """Initialize deployment configuration."""
    pass

def handle_deploy_command(args):
    """Handle deployment to Lambda or K8s."""
    if len(args) < 2:
        print_deploy_usage()
        return
    
    platform = args[1]  # "lambda" or "k8s"
    if platform == "lambda":
        handle_lambda_deploy(args[2:])
    elif platform == "k8s":
        handle_k8s_deploy(args[2:])
```

**Tests:**
- Test each command routing
- Test argument parsing
- Test help messages
- Test error handling

**Acceptance Criteria:**
- [ ] All commands route correctly
- [ ] Help messages comprehensive
- [ ] Backward compatible with existing commands
- [ ] All tests passing

---

#### Task 1.6: Documentation (Day 3, 2 hours)
**Files**: 
- `docs/CONFIGURATION_REFERENCE.md`
- Updated `README.md`

**Requirements:**
- Document deploy.yaml format
- Document all configuration options
- Provide examples
- Update main README

**Acceptance Criteria:**
- [ ] Complete configuration reference
- [ ] Examples included
- [ ] README updated

---

### Phase 1 Deliverables

**Code:**
- `jvbundler/config.py` (200 lines)
- `jvbundler/renderer.py` (100 lines)
- `jvbundler/templates/deploy.yaml.template` (300 lines)
- `jvbundler/templates/Dockerfile.unified` (50 lines)
- Enhanced `jvbundler/cli.py` (+150 lines)

**Tests:**
- `tests/test_config.py` (15 tests)
- `tests/test_renderer.py` (8 tests)
- Updated `tests/test_cli.py` (+10 tests)

**Documentation:**
- `docs/CONFIGURATION_REFERENCE.md`
- Updated `README.md`

**Success Metrics:**
- [ ] All 33+ tests passing
- [ ] Can load and validate configuration
- [ ] Can render templates
- [ ] CLI structure in place
- [ ] Documentation complete

---

## Phase 2: Docker Build System (Days 3-6)

### Goal
Implement Docker image building, tagging, and pushing to any registry.

### Tasks

#### Task 2.1: Docker Builder Core (Day 4, 5 hours)
**File**: `jvbundler/docker_builder.py`

**Requirements:**
- Build Docker images
- Support build arguments
- Support multi-platform builds
- Tag images appropriately
- Use BuildKit for optimization
- Handle build errors gracefully

**Implementation:**
```python
class DockerBuilder:
    """Build and manage Docker images."""
    
    def __init__(self, app_root: Path, config: DeployConfig):
        self.app_root = app_root
        self.config = config
        self.client = docker.from_env()
    
    def build(self, platform: str = None) -> str:
        """Build Docker image."""
        pass
    
    def tag(self, image_id: str, tags: List[str]):
        """Tag image with multiple tags."""
        pass
    
    def push(self, image_name: str, registry: str) -> bool:
        """Push image to registry."""
        pass
    
    def _authenticate_registry(self, registry: str):
        """Authenticate with Docker registry."""
        pass
```

**Tests:**
- Build image (mocked)
- Tag image
- Push image (mocked)
- Handle build failures
- Multi-platform builds

**Acceptance Criteria:**
- [ ] Can build Docker images
- [ ] Supports build arguments
- [ ] Can tag images
- [ ] Handles errors gracefully
- [ ] All tests passing

---

#### Task 2.2: Registry Support (Day 5, 4 hours)
**File**: `jvbundler/registry.py`

**Requirements:**
- Support ECR authentication
- Support Docker Hub
- Support private registries
- Handle authentication tokens
- Validate registry URLs

**Implementation:**
```python
class RegistryAuth:
    """Handle Docker registry authentication."""
    
    @staticmethod
    def authenticate_ecr(region: str) -> dict:
        """Get ECR authentication token."""
        pass
    
    @staticmethod
    def authenticate_docker_hub(username: str, password: str) -> dict:
        """Authenticate with Docker Hub."""
        pass
    
    @staticmethod
    def authenticate_generic(registry: str, username: str, password: str) -> dict:
        """Authenticate with generic registry."""
        pass
```

**Tests:**
- ECR authentication (mocked)
- Docker Hub authentication
- Generic registry authentication
- Handle auth failures

**Acceptance Criteria:**
- [ ] ECR authentication works
- [ ] Docker Hub authentication works
- [ ] Generic registry support
- [ ] All tests passing

---

#### Task 2.3: Integration with Bundler (Day 6, 2 hours)

**Requirements:**
- Update bundler to use unified Dockerfile
- Support both old and new templates
- Ensure backward compatibility

**Acceptance Criteria:**
- [ ] Bundler uses new Dockerfile template
- [ ] Backward compatible
- [ ] All existing tests passing

---

### Phase 2 Deliverables

**Code:**
- `jvbundler/docker_builder.py` (300 lines)
- `jvbundler/registry.py` (150 lines)
- Updated `jvbundler/bundler.py` (+50 lines)

**Tests:**
- `tests/test_docker_builder.py` (12 tests)
- `tests/test_registry.py` (8 tests)

**Documentation:**
- `docs/DOCKER_BUILD.md`

**Success Metrics:**
- [ ] All 20+ tests passing
- [ ] Can build Docker images
- [ ] Can push to any registry
- [ ] Documentation complete

---

## Phase 3: AWS Lambda Deployment (Days 7-10)

### Goal
Complete end-to-end Lambda deployment including ECR, Lambda function, IAM, and API Gateway.

### Tasks

#### Task 3.1: ECR Operations (Day 7, 4 hours)
**File**: `jvbundler/aws/ecr.py`

**Requirements:**
- Create ECR repositories
- Check if repository exists
- Get repository URI
- Push images to ECR
- Handle ECR authentication

**Implementation:**
```python
class ECRManager:
    """Manage AWS ECR operations."""
    
    def __init__(self, region: str):
        self.region = region
        self.client = boto3.client('ecr', region_name=region)
    
    def create_repository(self, name: str) -> str:
        """Create ECR repository, return URI."""
        pass
    
    def repository_exists(self, name: str) -> bool:
        """Check if repository exists."""
        pass
    
    def get_repository_uri(self, name: str) -> str:
        """Get repository URI."""
        pass
    
    def get_auth_token(self) -> dict:
        """Get ECR authentication token."""
        pass
```

**Tests:**
- Create repository (mocked with moto)
- Check existing repository
- Get repository URI
- Get auth token
- Handle errors

**Acceptance Criteria:**
- [ ] Can create ECR repositories
- [ ] Can authenticate with ECR
- [ ] Error handling works
- [ ] All tests passing

---

#### Task 3.2: IAM Management (Day 7, 3 hours)
**File**: `jvbundler/aws/iam.py`

**Requirements:**
- Create Lambda execution roles
- Attach policies
- Check if role exists
- Validate permissions

**Implementation:**
```python
class IAMManager:
    """Manage IAM roles and policies."""
    
    def __init__(self):
        self.client = boto3.client('iam')
    
    def create_lambda_role(self, role_name: str, policies: List[str]) -> str:
        """Create Lambda execution role."""
        pass
    
    def role_exists(self, role_name: str) -> bool:
        """Check if role exists."""
        pass
    
    def attach_policy(self, role_name: str, policy_arn: str):
        """Attach policy to role."""
        pass
```

**Tests:**
- Create role (mocked)
- Attach policies
- Check existing role
- Handle errors

**Acceptance Criteria:**
- [ ] Can create IAM roles
- [ ] Can attach policies
- [ ] Error handling works
- [ ] All tests passing

---

#### Task 3.3: Lambda Function Management (Day 8, 5 hours)
**File**: `jvbundler/aws/lambda_deployer.py`

**Requirements:**
- Create Lambda functions from container images
- Update existing functions
- Configure function settings (memory, timeout, etc.)
- Configure EFS mounts
- Configure VPC settings
- Wait for function to be active

**Implementation:**
```python
class LambdaDeployer:
    """Deploy Lambda functions."""
    
    def __init__(self, config: DeployConfig):
        self.config = config
        self.client = boto3.client('lambda', region_name=config.lambda_region)
    
    def create_function(self, image_uri: str, role_arn: str) -> dict:
        """Create Lambda function."""
        pass
    
    def update_function_code(self, function_name: str, image_uri: str) -> dict:
        """Update function code."""
        pass
    
    def update_function_config(self, function_name: str) -> dict:
        """Update function configuration."""
        pass
    
    def function_exists(self, function_name: str) -> bool:
        """Check if function exists."""
        pass
    
    def wait_for_function_active(self, function_name: str):
        """Wait for function to be active."""
        pass
    
    def deploy(self, image_uri: str, role_arn: str) -> dict:
        """Complete deployment workflow."""
        pass
```

**Tests:**
- Create function (mocked)
- Update function code
- Update function config
- Check existing function
- Wait for active state
- Full deployment workflow

**Acceptance Criteria:**
- [ ] Can create Lambda functions
- [ ] Can update functions
- [ ] Configuration works correctly
- [ ] EFS/VPC support
- [ ] All tests passing

---

#### Task 3.4: API Gateway Setup (Day 9, 5 hours)
**File**: `jvbundler/aws/api_gateway.py`

**Requirements:**
- Create HTTP API
- Configure routes
- Integrate with Lambda
- Configure CORS
- Set up custom domains (optional)
- Configure throttling

**Implementation:**
```python
class APIGatewayManager:
    """Manage API Gateway."""
    
    def __init__(self, config: DeployConfig):
        self.config = config
        self.client = boto3.client('apigatewayv2', 
                                   region_name=config.lambda_region)
    
    def create_api(self) -> str:
        """Create HTTP API."""
        pass
    
    def create_integration(self, api_id: str, function_arn: str) -> str:
        """Create Lambda integration."""
        pass
    
    def create_route(self, api_id: str, integration_id: str):
        """Create route."""
        pass
    
    def create_stage(self, api_id: str) -> str:
        """Create stage."""
        pass
    
    def configure_cors(self, api_id: str):
        """Configure CORS."""
        pass
    
    def get_api_url(self, api_id: str, stage_name: str) -> str:
        """Get API URL."""
        pass
    
    def deploy(self, function_arn: str) -> str:
        """Complete API Gateway setup."""
        pass
```

**Tests:**
- Create API (mocked)
- Create integration
- Create routes
- Configure CORS
- Get API URL
- Full deployment

**Acceptance Criteria:**
- [ ] Can create HTTP API
- [ ] Lambda integration works
- [ ] CORS configuration works
- [ ] Returns API URL
- [ ] All tests passing

---

#### Task 3.5: Lambda Deployment Orchestration (Day 10, 4 hours)
**File**: Enhanced `jvbundler/cli.py` - Lambda deployment handler

**Requirements:**
- Orchestrate complete Lambda deployment
- Build → Push ECR → Update Lambda → Setup API Gateway
- Handle each step's errors
- Provide progress feedback
- Support dry-run mode

**Implementation:**
```python
def handle_lambda_deploy(args: List[str], config: DeployConfig):
    """Handle complete Lambda deployment."""
    
    # Parse flags
    should_build = "--build" in args or "--all" in args
    should_push = "--push" in args or "--all" in args
    should_update = "--update" in args or "--all" in args
    should_create_api = "--create-api" in args or "--all" in args
    dry_run = "--dry-run" in args
    
    if dry_run:
        print_lambda_dry_run(config)
        return
    
    # Step 1: Build Docker image
    if should_build:
        logger.info("Building Docker image...")
        builder = DockerBuilder(app_root, config)
        image_id = builder.build()
    
    # Step 2: Push to ECR
    if should_push:
        logger.info("Pushing to ECR...")
        ecr = ECRManager(config.lambda_region)
        repo_uri = ecr.create_repository(config.image_name)
        builder.push(image_id, repo_uri)
    
    # Step 3: Setup IAM role
    logger.info("Setting up IAM role...")
    iam = IAMManager()
    role_arn = iam.create_lambda_role(...)
    
    # Step 4: Deploy Lambda function
    if should_update:
        logger.info("Deploying Lambda function...")
        deployer = LambdaDeployer(config)
        result = deployer.deploy(image_uri, role_arn)
    
    # Step 5: Setup API Gateway
    if should_create_api:
        logger.info("Setting up API Gateway...")
        api_gw = APIGatewayManager(config)
        api_url = api_gw.deploy(result['FunctionArn'])
    
    print(f"\n✓ Lambda deployment complete!")
    print(f"  Function: {result['FunctionName']}")
    print(f"  API URL: {api_url}")
```

**Acceptance Criteria:**
- [ ] Complete end-to-end deployment works
- [ ] Each step has progress feedback
- [ ] Errors handled gracefully
- [ ] Dry-run mode works
- [ ] Integration tests pass

---

### Phase 3 Deliverables

**Code:**
- `jvbundler/aws/__init__.py`
- `jvbundler/aws/ecr.py` (200 lines)
- `jvbundler/aws/iam.py` (150 lines)
- `jvbundler/aws/lambda_deployer.py` (400 lines)
- `jvbundler/aws/api_gateway.py` (300 lines)
- Enhanced `jvbundler/cli.py` (+200 lines)

**Tests:**
- `tests/aws/__init__.py`
- `tests/aws/test_ecr.py` (10 tests)
- `tests/aws/test_iam.py` (8 tests)
- `tests/aws/test_lambda_deployer.py` (15 tests)
- `tests/aws/test_api_gateway.py` (12 tests)
- Integration test for Lambda deployment

**Documentation:**
- `docs/LAMBDA_DEPLOYMENT.md`
- Example configurations

**Success Metrics:**
- [ ] All 45+ tests passing
- [ ] End-to-end Lambda deployment works
- [ ] Can deploy to real AWS account
- [ ] Documentation complete
- [ ] Example configurations provided

---

## Phase 4: Kubernetes Deployment (Days 11-15)

### Goal
Complete end-to-end Kubernetes deployment with manifest generation and kubectl integration.

### Tasks

#### Task 4.1: Kubernetes Manifest Templates (Day 11, 4 hours)
**Files**: `jvbundler/k8s/templates/*.j2`

**Requirements:**
- Deployment manifest template
- Service manifest template
- ConfigMap manifest template
- PVC manifest template
- Ingress manifest template
- HPA manifest template (optional)

**Templates to Create:**
- `deployment.yaml.j2`
- `service.yaml.j2`
- `configmap.yaml.j2`
- `pvc.yaml.j2`
- `ingress.yaml.j2`

**Acceptance Criteria:**
- [ ] All templates created
- [ ] Templates render correctly
- [ ] Support all configuration options
- [ ] Validated with kubectl

---

#### Task 4.2: Manifest Generator (Day 11-12, 5 hours)
**File**: `jvbundler/k8s/manifests.py`

**Requirements:**
- Render Kubernetes manifests from templates
- Validate manifests
- Support multiple manifest types
- Handle conditional rendering

**Implementation:**
```python
class ManifestGenerator:
    """Generate Kubernetes manifests."""
    
    def __init__(self, config: DeployConfig):
        self.config = config
        self.renderer = TemplateRenderer(Path(__file__).parent / "templates")
    
    def generate_deployment(self) -> str:
        """Generate deployment manifest."""
        pass
    
    def generate_service(self) -> str:
        """Generate service manifest."""
        pass
    
    def generate_configmap(self) -> str:
        """Generate configmap manifest."""
        pass
    
    def generate_pvc(self) -> str:
        """Generate PVC manifest."""
        pass
    
    def generate_ingress(self) -> str:
        """Generate ingress manifest."""
        pass
    
    def generate_all(self) -> List[str]:
        """Generate all manifests."""
        pass
    
    def save_manifests(self, output_dir: Path):
        """Save manifests to directory."""
        pass
```

**Tests:**
- Generate each manifest type
- Validate manifest YAML
- Handle missing optional fields
- Save manifests to files

**Acceptance Criteria:**
- [ ] Can generate all manifest types
- [ ] Manifests are valid YAML
- [ ] Conditional rendering works
- [ ] All tests passing

---

#### Task 4.3: kubectl Wrapper (Day 12, 4 hours)
**File**: `jvbundler/k8s/kubectl.py`

**Requirements:**
- Execute kubectl commands
- Handle context switching
- Stream command output
- Validate kubectl availability
- Parse kubectl output

**Implementation:**
```python
class KubectlWrapper:
    """Wrapper for kubectl commands."""
    
    def __init__(self, context: str = None, namespace: str = "default"):
        self.context = context
        self.namespace = namespace
        self._validate_kubectl()
    
    def apply(self, manifest: str, dry_run: bool = False) -> bool:
        """Apply manifest."""
        pass
    
    def delete(self, resource_type: str, name: str) -> bool:
        """Delete resource."""
        pass
    
    def get(self, resource_type: str, name: str = None) -> dict:
        """Get resource(s)."""
        pass
    
    def logs(self, pod_name: str, follow: bool = False, tail: int = None):
        """Get pod logs."""
        pass
    
    def rollout_status(self, deployment_name: str) -> str:
        """Check rollout status."""
        pass
    
    def _execute(self, args: List[str]) -> subprocess.CompletedProcess:
        """Execute kubectl command."""
        pass
```

**Tests:**
- Execute commands (mocked)
- Context switching
- Namespace handling
- Output parsing
- Error handling

**Acceptance Criteria:**
- [ ] Can execute kubectl commands
- [ ] Context/namespace handling works
- [ ] Output parsing correct
- [ ] All tests passing

---

#### Task 4.4: Kubernetes Deployer (Day 13-14, 8 hours)
**File**: `jvbundler/k8s/k8s_deployer.py`

**Requirements:**
- Apply manifests to cluster
- Wait for rollout completion
- Verify deployment health
- Handle deployment failures
- Support rollback

**Implementation:**
```python
class K8sDeployer:
    """Deploy to Kubernetes."""
    
    def __init__(self, config: DeployConfig):
        self.config = config
        self.kubectl = KubectlWrapper(
            context=config.k8s_context,
            namespace=config.k8s_namespace
        )
        self.manifest_gen = ManifestGenerator(config)
    
    def deploy(self, dry_run: bool = False) -> bool:
        """Complete Kubernetes deployment."""
        pass
    
    def apply_manifests(self, manifests: List[str]) -> bool:
        """Apply all manifests."""
        pass
    
    def wait_for_rollout(self, deployment_name: str, timeout: int = 300) -> bool:
        """Wait for deployment rollout."""
        pass
    
    def verify_health(self, deployment_name: str) -> bool:
        """Verify deployment health."""
        pass
    
    def rollback(self, deployment_name: str):
        """Rollback deployment."""
        pass
    
    def get_service_url(self, service_name: str) -> str:
        """Get service external URL."""
        pass
```

**Tests:**
- Apply manifests (mocked)
- Wait for rollout
- Verify health checks
- Rollback functionality
- Get service URL
- Full deployment workflow

**Acceptance Criteria:**
- [ ] Can deploy to Kubernetes
- [ ] Rollout wait works
- [ ] Health verification works
- [ ] Rollback supported
- [ ] All tests passing

---

#### Task 4.5: K8s Deployment Orchestration (Day 15, 4 hours)
**File**: Enhanced `jvbundler/cli.py` - K8s deployment handler

**Requirements:**
- Orchestrate complete K8s deployment
- Build → Push Registry → Apply Manifests
- Handle each step's errors
- Provide progress feedback
- Support dry-run mode

**Implementation:**
```python
def handle_k8s_deploy(args: List[str], config: DeployConfig):
    """Handle complete K8s deployment."""
    
    # Parse flags
    should_build = "--build" in args or "--all" in args
    should_push = "--push" in args or "--all" in args
    should_apply = "--apply" in args or "--all" in args
    dry_run = "--dry-run" in args
    
    if dry_run:
        print_k8s_dry_run(config)
        return
    
    # Step 1: Build Docker image
    if should_build:
        logger.info("Building Docker image...")
        builder = DockerBuilder(app_root, config)
        image_id = builder.build()
    
    # Step 2: Push to registry
    if should_push:
        logger.info("Pushing to registry...")
        registry_url = config.k8s_registry_url
        builder.push(image_id, registry_url)
    
    # Step 3: Apply manifests
    if should_apply:
        logger.info("Applying Kubernetes manifests...")
        deployer = K8sDeployer(config)
        result = deployer.deploy()
    
    # Step 4: Wait for rollout
    logger.info("Waiting for rollout...")
    deployer.wait_for_rollout(config.app_name)
    
    # Step 5: Get service URL
    service_url = deployer.get_service_url(config.app_name)
    
    print(f"\n✓ Kubernetes deployment complete!")
    print(f"  Namespace: {config.k8s_namespace}")
    print(f"  Service URL: {service_url}")
```

**Acceptance Criteria:**
- [ ] Complete end-to-end deployment works
- [ ] Progress feedback clear
- [ ] Errors handled gracefully
- [ ] Dry-run mode works
- [ ] Integration tests pass

---

### Phase 4 Deliverables

**Code:**
- `jvbundler/k8s/__init__.py`
- `jvbundler/k8s/manifests.py` (300 lines)
- `jvbundler/k8s/kubectl.py` (250 lines)
- `jvbundler/k8s/k8s_deployer.py` (400 lines)
- `jvbundler/k8s/templates/*.j2` (5 files, ~500 lines total)
- Enhanced `jvbundler/cli.py` (+200 lines)

**Tests:**
- `tests/k8s/__init__.py`
- `tests/k8s/test_manifests.py` (12 tests)
- `tests/k8s/test_kubectl.py` (10 tests)