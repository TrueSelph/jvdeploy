# jvbundler vs jvagent bundle - Comparison

This document outlines the differences and similarities between `jvbundler` (standalone tool) and `jvagent bundle` (built-in command).

## Overview

`jvbundler` is a **standalone, isolated version** of the bundling functionality that was originally part of `jvagent`. It has been extracted into its own package to:

1. **Separation of Concerns**: Bundling logic is independent of jvagent runtime
2. **Lighter Dependencies**: Only requires PyYAML, not the full jvagent stack
3. **Reusability**: Can be used in CI/CD pipelines without installing jvagent
4. **Modularity**: Easier to maintain and test in isolation

## Feature Comparison

| Feature | jvagent bundle | jvbundler |
|---------|---------------|-----------|
| **Dependency Discovery** | ✅ | ✅ |
| **Dockerfile Generation** | ✅ | ✅ |
| **App Validation** | ✅ | ✅ |
| **Layer Caching** | ✅ | ✅ |
| **Base Template Support** | ✅ | ✅ |
| **Standalone Installation** | ❌ (requires jvagent) | ✅ |
| **CLI Interface** | ✅ | ✅ |
| **Python API** | ✅ | ✅ |
| **Debug Logging** | ✅ | ✅ |
| **Version Specifiers** | ✅ | ✅ |

## Usage Comparison

### jvagent bundle

```bash
# From current directory
cd /path/to/jvagent_app
jvagent bundle

# With app path as argument
jvagent bundle /path/to/jvagent_app

# With app path before command
jvagent /path/to/jvagent_app bundle
```

### jvbundler

```bash
# From current directory
cd /path/to/jvagent_app
jvbundler

# With app path as argument
jvbundler /path/to/jvagent_app

# With debug flag
jvbundler --debug /path/to/jvagent_app
```

## Installation Comparison

### jvagent bundle

Requires full jvagent installation:

```bash
pip install jvagent
# Installs: jvspatial, python-dotenv, pyyaml, httpx, jinja2, dspy, and more
```

### jvbundler

Minimal dependencies:

```bash
pip install jvbundler
# Installs: pyyaml only
```

## Implementation Details

Both implementations:

1. **Share the same core logic**: The bundling algorithm is identical
2. **Use the same directory structure**: Both expect the same jvagent app layout
3. **Generate identical Dockerfiles**: Output format is the same
4. **Support the same info.yaml format**: Action dependencies are discovered the same way

### Key Differences

#### 1. Dependencies

**jvagent bundle:**
- Requires full jvagent installation
- Dependencies: jvspatial, python-dotenv, pyyaml, httpx, jinja2, dspy
- Size: ~50MB+ with all dependencies

**jvbundler:**
- Minimal dependencies
- Dependencies: pyyaml only
- Size: ~5MB with dependencies

#### 2. Import Paths

**jvagent bundle:**
```python
from jvagent.bundle import Bundler
```

**jvbundler:**
```python
from jvbundler import Bundler
```

#### 3. CLI Entry Point

**jvagent bundle:**
```python
# In jvagent/cli.py
@cli.command()
def bundle(app_root):
    from jvagent.bundle import Bundler
    bundler = Bundler(app_root)
    bundler.generate_dockerfile()
```

**jvbundler:**
```python
# In jvbundler/cli.py
def main():
    from jvbundler import Bundler
    bundler = Bundler(app_root)
    bundler.generate_dockerfile()
```

## When to Use Each

### Use `jvagent bundle` when:

- You already have jvagent installed
- You're developing jvagent applications locally
- You want a single tool for all jvagent operations
- You're running jvagent in development mode

### Use `jvbundler` when:

- You want a lightweight bundling tool
- You're using it in CI/CD pipelines
- You don't need the full jvagent runtime
- You want faster installation times
- You're creating Docker build processes
- You want to minimize container image sizes

## Migration Guide

### From jvagent bundle to jvbundler

**Step 1: Install jvbundler**
```bash
pip install jvbundler
```

**Step 2: Update your scripts**
```bash
# Before
jvagent bundle /path/to/app

# After
jvbundler /path/to/app
```

**Step 3: Update Python code**
```python
# Before
from jvagent.bundle import Bundler

# After
from jvbundler import Bundler
```

### From jvbundler to jvagent bundle

**Step 1: Install jvagent**
```bash
pip install jvagent
```

**Step 2: Update your scripts**
```bash
# Before
jvbundler /path/to/app

# After
jvagent bundle /path/to/app
```

**Step 3: Update Python code**
```python
# Before
from jvbundler import Bundler

# After
from jvagent.bundle import Bundler
```

## CI/CD Recommendations

### GitHub Actions

For CI/CD pipelines, use `jvbundler` for faster installation:

```yaml
name: Build Docker Image

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      # Lightweight option (recommended)
      - name: Install jvbundler
        run: pip install jvbundler
      
      - name: Generate Dockerfile
        run: jvbundler /path/to/app
      
      - name: Build Docker image
        run: docker build -t myapp:latest /path/to/app
```

### GitLab CI

```yaml
build:
  image: python:3.12
  script:
    - pip install jvbundler
    - jvbundler /path/to/app
    - docker build -t myapp:latest /path/to/app
```

## Performance Comparison

### Installation Time

| Tool | Installation Time | Dependencies Installed |
|------|------------------|----------------------|
| jvagent | ~30-60 seconds | 15+ packages |
| jvbundler | ~5-10 seconds | 1 package |

### Docker Layer Caching

Both tools generate identical Dockerfiles with optimal layer caching:

```dockerfile
# Each action gets its own RUN command for better caching
RUN /opt/venv/bin/pip install --no-cache-dir openai>=1.0.0 httpx>=0.24.0
RUN /opt/venv/bin/pip install --no-cache-dir requests>=2.31.0 pydantic>=2.0.0
```

## Testing

### jvagent bundle

Tested as part of the jvagent test suite:
```bash
cd jvagent
pytest tests/
```

### jvbundler

Has its own comprehensive test suite:
```bash
cd jvbundler
pytest tests/
# 52 tests covering all functionality
```

## Maintenance

### jvagent bundle

- Maintained as part of jvagent
- Updates require jvagent version bump
- Changes affect jvagent users

### jvbundler

- Maintained independently
- Can be updated without affecting jvagent
- Follows semantic versioning independently

## Future Considerations

Both tools will continue to:

- Support the same jvagent app structure
- Generate compatible Dockerfiles
- Maintain feature parity for core bundling functionality

jvbundler may add:
- Additional template options
- More customization features
- Extended CLI options
- Integration with other tools

## Conclusion

Choose `jvbundler` for:
- ✅ Lightweight deployments
- ✅ CI/CD pipelines
- ✅ Standalone bundling needs
- ✅ Faster installation

Choose `jvagent bundle` for:
- ✅ Full jvagent development
- ✅ When you already have jvagent
- ✅ Integrated tooling needs

Both tools produce **identical results** and use the **same core logic**. The choice comes down to your deployment context and whether you need the full jvagent runtime or just the bundling functionality.