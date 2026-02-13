"""Tests for CLI env command."""

import sys
from pathlib import Path

import pytest
import yaml

from jvdeploy.cli import main


def test_env_lambda_lifecycle(temp_dir, capsys, monkeypatch):
    """Test full lifecycle of lambda env vars."""
    app_root = temp_dir / "test_app"
    app_root.mkdir()
    config_path = app_root / "deploy.yaml"

    # Initial config
    config = {
        "version": "1.0",
        "app": {"name": "test"},
        "image": {"name": "test"},
        "lambda": {"enabled": True, "environment": {"EXISTING": "value"}},
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # List
    # For list, app_root positional works
    monkeypatch.setattr(
        sys,
        "argv",
        ["jvdeploy", "env", "lambda", "list", "--config", "deploy.yaml", str(app_root)],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    assert "EXISTING=value" in out

    # Set - chdir instead of passing path
    monkeypatch.chdir(app_root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["jvdeploy", "env", "lambda", "set", "NEW=var", "--config", "deploy.yaml"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    assert "Environment variables updated" in out

    # Verify set in file
    with open(config_path) as f:
        new_config = yaml.safe_load(f)
    assert new_config["lambda"]["environment"]["NEW"] == "var"

    # Delete - chdir
    monkeypatch.chdir(app_root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["jvdeploy", "env", "lambda", "delete", "EXISTING", "--config", "deploy.yaml"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    assert "Deleted EXISTING" in out

    # Verify delete in file
    with open(config_path) as f:
        final_config = yaml.safe_load(f)
    assert "EXISTING" not in final_config["lambda"]["environment"]
    assert final_config["lambda"]["environment"]["NEW"] == "var"


def test_env_k8s_lifecycle(temp_dir, capsys, monkeypatch):
    """Test full lifecycle of k8s env vars."""
    app_root = temp_dir / "test_app_k8s"
    app_root.mkdir()
    config_path = app_root / "deploy.yaml"

    # Initial config
    config = {
        "version": "1.0",
        "app": {"name": "test"},
        "image": {"name": "test"},
        "kubernetes": {
            "enabled": True,
            "deployment": {"container": {"environment": {"K8S_VAR": "val"}}},
        },
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # List (using kubernetes alias)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "jvdeploy",
            "env",
            "kubernetes",
            "list",
            "--config",
            "deploy.yaml",
            str(app_root),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    assert "K8S_VAR=val" in out

    # Set (using k8s alias) - chdir
    monkeypatch.chdir(app_root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["jvdeploy", "env", "k8s", "set", "NEW_K8S=new_val", "--config", "deploy.yaml"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0

    # Verify set in file
    with open(config_path) as f:
        new_config = yaml.safe_load(f)
    assert (
        new_config["kubernetes"]["deployment"]["container"]["environment"]["NEW_K8S"]
        == "new_val"
    )


def test_env_list_formats(temp_dir, capsys, monkeypatch):
    """Test list formats (json, table)."""
    app_root = temp_dir / "test_app_fmt"
    app_root.mkdir()
    config_path = app_root / "deploy.yaml"

    config = {
        "version": "1.0",
        "app": {"name": "test"},
        "image": {"name": "test"},
        "lambda": {"enabled": True, "environment": {"A": "1", "B": "2"}},
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # JSON
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "jvdeploy",
            "env",
            "lambda",
            "list",
            "--json",
            "--config",
            "deploy.yaml",
            str(app_root),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    import json

    data = json.loads(out)
    assert data["A"] == "1"
    assert data["B"] == "2"

    # Table
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "jvdeploy",
            "env",
            "lambda",
            "list",
            "--table",
            "--config",
            "deploy.yaml",
            str(app_root),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    assert "KEY" in out
    assert "VALUE" in out
    assert "A" in out
    assert "1" in out
