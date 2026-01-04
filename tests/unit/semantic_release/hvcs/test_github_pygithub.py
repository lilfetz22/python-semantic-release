"""Tests for PyGithub integration in Github HVCS"""

from __future__ import annotations

from unittest import mock

import pytest

from semantic_release.hvcs.github import Github


@pytest.fixture
def mock_github_client():
    """Mock the PyGithub Github client"""
    with mock.patch("semantic_release.hvcs.github.GithubClient") as mock_client:
        yield mock_client


@pytest.fixture
def mock_github_repo():
    """Mock a PyGithub repository object"""
    return mock.Mock()


def test_pygithub_client_initialization_default(mock_github_client):
    """Test that PyGithub client is initialized correctly for github.com"""
    # Arrange
    token = "test_token_123"
    remote_url = "git@github.com:test-owner/test-repo.git"

    # Act
    with mock.patch("semantic_release.hvcs.github.Auth") as mock_auth:
        github_hvcs = Github(remote_url=remote_url, token=token)

    # Assert
    # Auth.Token should be called with the token
    mock_auth.Token.assert_called_once_with(token)

    # GithubClient should be initialized WITHOUT base_url for github.com
    mock_github_client.assert_called_once_with(auth=mock_auth.Token.return_value)

    # Verify attributes
    assert github_hvcs.token == token
    assert github_hvcs.hvcs_api_domain == Github.DEFAULT_API_DOMAIN


def test_pygithub_client_initialization_enterprise(mock_github_client):
    """Test that PyGithub client is initialized with base_url for GitHub Enterprise"""
    # Arrange
    token = "enterprise_token"
    remote_url = "git@github.enterprise.com:test-owner/test-repo.git"
    enterprise_domain = "github.enterprise.com"
    enterprise_api_domain = "github.enterprise.com/api/v3"

    # Act
    with mock.patch("semantic_release.hvcs.github.Auth") as mock_auth:
        github_hvcs = Github(
            remote_url=remote_url,
            hvcs_domain=enterprise_domain,
            hvcs_api_domain=enterprise_api_domain,
            token=token,
        )

    # Assert
    # Auth.Token should be called with the token
    mock_auth.Token.assert_called_once_with(token)

    # GithubClient should be initialized WITH base_url for Enterprise
    expected_base_url = f"https://{enterprise_api_domain}"
    mock_github_client.assert_called_once_with(
        auth=mock_auth.Token.return_value, base_url=expected_base_url
    )

    # Verify attributes
    assert github_hvcs.hvcs_api_domain == enterprise_api_domain


def test_pygithub_client_initialization_no_token(mock_github_client):
    """Test that PyGithub client is initialized with None auth when no token provided"""
    # Arrange
    remote_url = "git@github.com:test-owner/test-repo.git"

    # Act
    with mock.patch("semantic_release.hvcs.github.Auth") as mock_auth:
        Github(remote_url=remote_url, token=None)

    # Assert
    # Auth.Token should NOT be called without a token
    mock_auth.Token.assert_not_called()

    # GithubClient should be initialized with auth=None
    mock_github_client.assert_called_once_with(auth=None)


def test_repo_property_lazy_loading(mock_github_client, mock_github_repo):
    """Test that the repo property lazily loads and caches the repository"""
    # Arrange
    remote_url = "git@github.com:test-owner/test-repo.git"
    token = "test_token"

    # Mock the client instance and its get_repo method
    mock_client_instance = mock.Mock()
    mock_client_instance.get_repo.return_value = mock_github_repo
    mock_github_client.return_value = mock_client_instance

    # Act
    github_hvcs = Github(remote_url=remote_url, token=token)

    # Verify repo is not fetched yet
    assert github_hvcs._repo is None
    mock_client_instance.get_repo.assert_not_called()

    # Access the repo property (should trigger lazy loading)
    repo = github_hvcs.repo

    # Assert
    # get_repo should be called with the correct owner/repo
    mock_client_instance.get_repo.assert_called_once_with("test-owner/test-repo")
    assert repo == mock_github_repo

    # Access repo again (should use cached value)
    repo2 = github_hvcs.repo
    assert repo2 == mock_github_repo

    # get_repo should still only be called once (cached)
    assert mock_client_instance.get_repo.call_count == 1


def test_repo_property_with_github_repository_env(
    mock_github_client, mock_github_repo, monkeypatch
):
    """Test that repo property uses GITHUB_REPOSITORY environment variable"""
    # Arrange
    monkeypatch.setenv("GITHUB_REPOSITORY", "env-owner/env-repo")
    remote_url = "git@github.com:test-owner/test-repo.git"
    token = "test_token"

    # Mock the client instance and its get_repo method
    mock_client_instance = mock.Mock()
    mock_client_instance.get_repo.return_value = mock_github_repo
    mock_github_client.return_value = mock_client_instance

    # Act
    github_hvcs = Github(remote_url=remote_url, token=token)
    repo = github_hvcs.repo

    # Assert
    # Should use owner/name from environment variable, not parsed from URL
    mock_client_instance.get_repo.assert_called_once_with("env-owner/env-repo")
    assert repo == mock_github_repo


def test_repo_property_handles_github_exception(mock_github_client):
    """Test that repo property properly raises exception when get_repo fails"""
    # Arrange
    from github import GithubException

    remote_url = "git@github.com:test-owner/test-repo.git"
    token = "test_token"

    # Mock the client instance to raise GithubException
    mock_client_instance = mock.Mock()
    mock_client_instance.get_repo.side_effect = GithubException(
        status=404, data={"message": "Not Found"}, headers={}
    )
    mock_github_client.return_value = mock_client_instance

    # Act & Assert
    github_hvcs = Github(remote_url=remote_url, token=token)

    with pytest.raises(GithubException):
        _ = github_hvcs.repo
