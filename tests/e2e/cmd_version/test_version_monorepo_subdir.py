from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from git import Repo

from tests.const import MAIN_PROG_NAME, VERSION_SUBCMD

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import RunCliFn


@pytest.fixture
def monorepo_subdirectory(tmp_path: Path) -> Path:
    """Create a minimal monorepo layout with .git/ at the root and a package subdirectory."""
    # Initialize git repo at the root
    repo = Repo.init(str(tmp_path))

    # Create a minimal pyproject.toml in the subdirectory with repo_dir = ".."
    pkg_dir = tmp_path / "package-a"
    pkg_dir.mkdir()

    pyproject_content = """\
[project]
name = "package-a"
version = "0.0.0"

[tool.semantic_release]
repo_dir = ".."
"""
    (pkg_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # Create a dummy file and initial commit so repo is not empty
    readme = tmp_path / "README.md"
    readme.write_text("# Monorepo\n", encoding="utf-8")
    repo.index.add([str(readme), str(pkg_dir / "pyproject.toml")])
    repo.index.commit("Initial commit")

    # Add a fake origin remote (required by CLI)
    repo.create_remote("origin", "https://github.com/fake-owner/fake-monorepo.git")

    return pkg_dir


def test_no_false_git_warning_from_monorepo_subdirectory(
    monorepo_subdirectory: Path,
    run_cli: RunCliFn,
):
    """
    Given a monorepo where .git/ is in the parent directory and repo_dir is set to '..',
    When running `semantic-release version --print` from the package subdirectory,
    Then no false 'does not match the detected git repository root' warning is emitted
    and the command exits successfully.

    Regression test for https://github.com/python-semantic-release/python-semantic-release/issues/1418
    """
    original_dir = os.getcwd()
    os.chdir(str(monorepo_subdirectory))

    try:
        cli_cmd = [MAIN_PROG_NAME, VERSION_SUBCMD, "--print"]
        result = run_cli(cli_cmd[1:])
    finally:
        os.chdir(original_dir)

    # The command should not fail outright
    assert result.exit_code == 0, (
        f"CLI exited with code {result.exit_code}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )

    # The key assertion: no false warning about .git/ in higher parent directory
    assert "does not match the detected git repository root" not in result.stderr
