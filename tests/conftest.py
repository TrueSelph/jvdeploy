"""Shared pytest fixtures for jvdeploy tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_jvagent_app(temp_dir: Path) -> Path:
    """Create a mock jvagent application structure for testing.

    Creates:
        - app.yaml
        - agents/myorg/agent1/actions/myorg/action1/info.yaml
        - agents/myorg/agent1/actions/myorg/action2/info.yaml
        - agents/other/agent2/actions/other/action3/info.yaml
    """
    app_root = temp_dir / "test_app"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\nversion: 0.1.0\n")

    # Create first action with dependencies
    action1_path = app_root / "agents" / "myorg" / "agent1" / "actions" / "myorg" / "action1"
    action1_path.mkdir(parents=True)
    action1_info = action1_path / "info.yaml"
    action1_info.write_text(
        """package:
  name: myorg/action1
  dependencies:
    pip:
      - openai>=1.0.0
      - httpx>=0.24.0
"""
    )

    # Create second action with dependencies
    action2_path = app_root / "agents" / "myorg" / "agent1" / "actions" / "myorg" / "action2"
    action2_path.mkdir(parents=True)
    action2_info = action2_path / "info.yaml"
    action2_info.write_text(
        """package:
  name: myorg/action2
  dependencies:
    pip:
      - requests>=2.31.0
      - pydantic>=2.0.0
"""
    )

    # Create third action in different namespace
    action3_path = app_root / "agents" / "other" / "agent2" / "actions" / "other" / "action3"
    action3_path.mkdir(parents=True)
    action3_info = action3_path / "info.yaml"
    action3_info.write_text(
        """package:
  name: other/action3
  dependencies:
    pip:
      - numpy>=1.24.0
"""
    )

    return app_root


@pytest.fixture
def mock_app_no_dependencies(temp_dir: Path) -> Path:
    """Create a mock jvagent app with no action dependencies."""
    app_root = temp_dir / "test_app_no_deps"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\nversion: 0.1.0\n")

    # Create action without dependencies
    action_path = app_root / "agents" / "myorg" / "agent1" / "actions" / "myorg" / "action1"
    action_path.mkdir(parents=True)
    action_info = action_path / "info.yaml"
    action_info.write_text(
        """package:
  name: myorg/action1
"""
    )

    return app_root


@pytest.fixture
def mock_app_no_agents(temp_dir: Path) -> Path:
    """Create a mock jvagent app with no agents directory."""
    app_root = temp_dir / "test_app_no_agents"
    app_root.mkdir()

    # Create app.yaml only
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\nversion: 0.1.0\n")

    return app_root


@pytest.fixture
def base_template_content() -> str:
    """Return base Dockerfile template content."""
    return """FROM registry.v75inc.dev/jvagent/jvagent-base:latest

WORKDIR /var/task
COPY . /var/task/

# {{ACTION_DEPENDENCIES}}
"""


@pytest.fixture
def mock_base_template(temp_dir: Path, base_template_content: str) -> Path:
    """Create a mock base Dockerfile template."""
    template_path = temp_dir / "Dockerfile.base"
    template_path.write_text(base_template_content)
    return template_path
