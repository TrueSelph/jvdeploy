"""Tests for CLI env remote command."""

import sys
from unittest.mock import patch

import pytest

from jvdeploy.cli import main


@pytest.fixture
def mock_lambda_deployer():
    """Mock lambda deployer."""

    with patch("jvdeploy.aws.LambdaDeployer") as mock:
        yield mock


def test_env_lambda_remote_list(mock_lambda_deployer, capsys, monkeypatch):
    """Test remote list command."""
    deployer_instance = mock_lambda_deployer.return_value
    deployer_instance.get_env_vars.return_value = {"REMOTE_VAR": "remote_val"}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "jvdeploy",
            "env",
            "lambda",
            "list",
            "--function",
            "my-func",
            "--region",
            "us-west-2",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    assert "REMOTE_VAR=remote_val" in out

    # Verify deployer called correctly
    mock_lambda_deployer.assert_called_with(
        {"region": "us-west-2", "function": {"name": "my-func"}}
    )
    deployer_instance.get_env_vars.assert_called_with("my-func")


def test_env_lambda_remote_set(mock_lambda_deployer, capsys, monkeypatch):
    """Test remote set command."""
    deployer_instance = mock_lambda_deployer.return_value
    deployer_instance.get_env_vars.return_value = {"EXISTING": "val"}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "jvdeploy",
            "env",
            "lambda",
            "set",
            "NEW=var",
            "--function",
            "my-func",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0

    # Verify update called with merged vars
    deployer_instance.update_env_vars.assert_called_with(
        {"EXISTING": "val", "NEW": "var"}, "my-func"
    )


def test_env_lambda_remote_delete(mock_lambda_deployer, capsys, monkeypatch):
    """Test remote delete command."""
    deployer_instance = mock_lambda_deployer.return_value
    deployer_instance.get_env_vars.return_value = {"A": "1", "B": "2"}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "jvdeploy",
            "env",
            "lambda",
            "delete",
            "A",
            "--function",
            "my-func",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    assert "Removed A" in out

    # Verify update called with removed vars
    deployer_instance.update_env_vars.assert_called_with({"B": "2"}, "my-func")
