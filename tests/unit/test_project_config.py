"""
Tests for project_config module.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from agents_lib.project_config import (
    ProjectConfig,
    load_project_config,
    get_project,
    reload_project_config,
)


def test_project_config_default_octavia():
    """Test default Octavia configuration when no config file exists."""
    config = {
        "project": {
            "name": "octavia",
            "slug": "octavia",
            "launchpad": "octavia",
            "repos": ["openstack/octavia"],
            "devstack_services": [
                "devstack@o-api.service",
                "devstack@o-cw.service"
            ]
        }
    }

    project = ProjectConfig(config)

    assert project.name == "octavia"
    assert project.slug == "octavia"
    assert project.launchpad == "octavia"
    assert project.repos == ["openstack/octavia"]
    assert len(project.devstack_services) == 2

    # Check derived paths
    assert project.triages_dir == "~/octavia_bug_triages"
    assert project.reviews_dir == "~/octavia_reviews"
    assert project.triage_tracking_file == "~/.octavia_bug_triages.json"
    assert project.review_tracking_file == "~/.octavia_reviewed_changes.json"


def test_project_config_ovn_octavia():
    """Test ovn-octavia-provider configuration."""
    config = {
        "project": {
            "name": "ovn-octavia-provider",
            "slug": "ovn-octavia",
            "launchpad": "neutron",
            "repos": [
                "openstack/networking-ovn",
                "openstack/ovn-octavia-provider"
            ],
            "devstack_services": [
                "devstack@q-ovn-metadata-agent.service",
                "devstack@ovn-controller.service"
            ]
        }
    }

    project = ProjectConfig(config)

    assert project.name == "ovn-octavia-provider"
    assert project.slug == "ovn-octavia"
    assert project.launchpad == "neutron"
    assert len(project.repos) == 2

    # Check derived paths use slug
    assert project.triages_dir == "~/ovn-octavia_bug_triages"
    assert project.reviews_dir == "~/ovn-octavia_reviews"
    assert project.triage_tracking_file == "~/.ovn-octavia_bug_triages.json"


def test_project_config_slug_auto_generation():
    """Test automatic slug generation from project name."""
    config = {
        "project": {
            "name": "My/Special-Project",
            # slug omitted - should be auto-generated
        }
    }

    project = ProjectConfig(config)

    assert project.name == "My/Special-Project"
    assert project.slug == "my-special-project"  # lowercase, slash replaced with dash


def test_project_config_custom_paths():
    """Test custom output paths override defaults."""
    config = {
        "project": {
            "name": "octavia",
            "slug": "octavia",
            "triages_dir": "/custom/triages",
            "triage_tracking_file": "/custom/tracking.json"
        }
    }

    project = ProjectConfig(config)

    assert project.triages_dir == "/custom/triages"
    assert project.triage_tracking_file == "/custom/tracking.json"
    # Other paths should still use defaults
    assert project.reviews_dir == "~/octavia_reviews"


def test_project_config_to_dict():
    """Test serialization to dictionary."""
    config = {
        "project": {
            "name": "octavia",
            "slug": "octavia",
            "launchpad": "octavia",
            "repos": ["openstack/octavia"]
        }
    }

    project = ProjectConfig(config)
    result = project.to_dict()

    assert result["name"] == "octavia"
    assert result["slug"] == "octavia"
    assert result["launchpad"] == "octavia"
    assert "triages_dir" in result
    assert "triage_tracking_file" in result


@patch.dict(os.environ, {"CLAUDE_AGENTS_PROJECT_CONFIG": ""}, clear=True)
def test_load_project_config_from_env(tmp_path):
    """Test loading from CLAUDE_AGENTS_PROJECT_CONFIG env var."""
    # Create a temporary config file
    config_file = tmp_path / "config.json"
    config_file.write_text('{"project": {"name": "test-env"}}')

    # Set env var to point to it
    os.environ["CLAUDE_AGENTS_PROJECT_CONFIG"] = str(config_file)

    project = load_project_config()

    assert project.name == "test-env"


def test_load_project_config_from_user_config(tmp_path, monkeypatch):
    """Test loading from ~/.config/claude-agents/project.json."""
    # Create user config directory structure
    user_config_dir = tmp_path / ".config" / "claude-agents"
    user_config_dir.mkdir(parents=True)
    config_file = user_config_dir / "project.json"
    config_file.write_text('{"project": {"name": "user-config"}}')

    # Mock Path.home() to return our tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    project = load_project_config()

    assert project.name == "user-config"


@patch("pathlib.Path.is_file")
def test_load_project_config_defaults_to_octavia(mock_is_file):
    """Test fallback to Octavia default when no config found."""
    mock_is_file.return_value = False

    project = load_project_config()

    assert project.name == "octavia"
    assert project.slug == "octavia"
    assert "openstack/octavia" in project.repos


def test_get_project_singleton():
    """Test get_project returns the singleton instance."""
    project1 = get_project()
    project2 = get_project()

    assert project1 is project2  # Same object


def test_reload_project_config(tmp_path, monkeypatch):
    """Test reload_project_config refreshes the singleton."""
    # Create a test config
    config_file = tmp_path / "test_project.json"
    config_file.write_text('{"project": {"name": "test-reload"}}')

    # Set env to use our test config
    monkeypatch.setenv("CLAUDE_AGENTS_PROJECT_CONFIG", str(config_file))

    # Reload should pick up the new config
    project = reload_project_config()

    assert project.name == "test-reload"


def test_project_config_empty_devstack_services():
    """Test handling of empty devstack services list."""
    config = {
        "project": {
            "name": "nova",
            "devstack_services": []
        }
    }

    project = ProjectConfig(config)

    assert project.devstack_services == []


def test_project_config_minimal():
    """Test minimal config with only project name."""
    config = {
        "project": {
            "name": "neutron"
        }
    }

    project = ProjectConfig(config)

    # Should generate sensible defaults
    assert project.name == "neutron"
    assert project.slug == "neutron"
    assert project.launchpad == "neutron"
    assert project.repos == ["openstack/neutron"]
    assert project.triages_dir == "~/neutron_bug_triages"


def test_project_config_all_tracking_files():
    """Test all tracking file paths are generated correctly."""
    config = {
        "project": {
            "name": "cinder",
            "slug": "cinder"
        }
    }

    project = ProjectConfig(config)

    assert project.triage_tracking_file == "~/.cinder_bug_triages.json"
    assert project.review_tracking_file == "~/.cinder_reviewed_changes.json"
    assert project.ci_tracking_file == "~/.cinder_ci_failures.json"
    assert project.reproduction_tracking_file == "~/.cinder_bug_reproductions.json"
    assert project.proposal_tracking_file == "~/.cinder_fix_proposals.json"
    assert project.verification_tracking_file == "~/.cinder_fix_verifications.json"


def test_project_config_all_output_dirs():
    """Test all output directory paths are generated correctly."""
    config = {
        "project": {
            "name": "keystone",
            "slug": "keystone"
        }
    }

    project = ProjectConfig(config)

    assert project.triages_dir == "~/keystone_bug_triages"
    assert project.reviews_dir == "~/keystone_reviews"
    assert project.ci_failures_dir == "~/keystone_ci_failures"
    assert project.reproductions_dir == "~/keystone_bug_reproductions"
    assert project.devstack_tests_dir == "~/keystone_devstack_tests"
    assert project.fix_proposals_dir == "~/keystone_fix_proposals"
    assert project.fix_verifications_dir == "~/keystone_fix_verifications"
