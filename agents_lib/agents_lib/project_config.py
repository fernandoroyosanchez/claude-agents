"""
Project configuration for Claude Agents.

Allows the agent system to work with any OpenStack project, not just Octavia.
Users specify their project once in a global config file, and all agents adapt
automatically (CLI commands, output paths, tracking files, repos, etc.).
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class ProjectConfig:
    """Project-specific configuration loaded from global config."""

    def __init__(self, config: dict):
        project = config.get("project", {})

        self.name = project.get("name", "octavia")
        self.slug = project.get("slug", self.name.lower().replace("/", "-"))
        self.launchpad = project.get("launchpad", self.slug)
        self.launchpad_tags = project.get("launchpad_tags", [])
        self.repos = project.get("repos", [f"openstack/{self.name}"])
        self.devstack_services = project.get("devstack_services", [])

        # Derived paths (use slug for filesystem safety)
        self.triages_dir = project.get("triages_dir", f"~/{self.slug}_bug_triages")
        self.reviews_dir = project.get("reviews_dir", f"~/{self.slug}_reviews")
        self.ci_failures_dir = project.get("ci_failures_dir", f"~/{self.slug}_ci_failures")
        self.reproductions_dir = project.get("reproductions_dir", f"~/{self.slug}_bug_reproductions")
        self.devstack_tests_dir = project.get("devstack_tests_dir", f"~/{self.slug}_devstack_tests")
        self.fix_proposals_dir = project.get("fix_proposals_dir", f"~/{self.slug}_fix_proposals")
        self.fix_verifications_dir = project.get("fix_verifications_dir", f"~/{self.slug}_fix_verifications")

        # Derived tracking files
        self.triage_tracking_file = project.get("triage_tracking_file", f"~/.{self.slug}_bug_triages.json")
        self.review_tracking_file = project.get("review_tracking_file", f"~/.{self.slug}_reviewed_changes.json")
        self.ci_tracking_file = project.get("ci_tracking_file", f"~/.{self.slug}_ci_failures.json")
        self.reproduction_tracking_file = project.get("reproduction_tracking_file", f"~/.{self.slug}_bug_reproductions.json")
        self.proposal_tracking_file = project.get("proposal_tracking_file", f"~/.{self.slug}_fix_proposals.json")
        self.verification_tracking_file = project.get("verification_tracking_file", f"~/.{self.slug}_fix_verifications.json")

    def to_dict(self) -> dict:
        """Return project config as a dictionary."""
        return {
            "name": self.name,
            "slug": self.slug,
            "launchpad": self.launchpad,
            "launchpad_tags": self.launchpad_tags,
            "repos": self.repos,
            "devstack_services": self.devstack_services,
            "triages_dir": self.triages_dir,
            "reviews_dir": self.reviews_dir,
            "ci_failures_dir": self.ci_failures_dir,
            "reproductions_dir": self.reproductions_dir,
            "devstack_tests_dir": self.devstack_tests_dir,
            "fix_proposals_dir": self.fix_proposals_dir,
            "fix_verifications_dir": self.fix_verifications_dir,
            "triage_tracking_file": self.triage_tracking_file,
            "review_tracking_file": self.review_tracking_file,
            "ci_tracking_file": self.ci_tracking_file,
            "reproduction_tracking_file": self.reproduction_tracking_file,
            "proposal_tracking_file": self.proposal_tracking_file,
            "verification_tracking_file": self.verification_tracking_file,
        }


def load_project_config() -> ProjectConfig:
    """Load global project configuration from standard locations.

    Search order:
    1. CLAUDE_AGENTS_PROJECT_CONFIG environment variable (path to JSON file)
    2. ~/.config/claude-agents/project.json
    3. <repo-root>/project.json
    4. Default to Octavia (backward compatibility)

    Returns:
        ProjectConfig instance with project settings.
    """
    candidates = []

    # 1. Environment variable override
    env_path = os.environ.get("CLAUDE_AGENTS_PROJECT_CONFIG")
    if env_path:
        candidates.append(Path(env_path))

    # 2. User config directory
    candidates.append(Path.home() / ".config" / "claude-agents" / "project.json")

    # 3. Repo root (this file is agents_lib/agents_lib/project_config.py)
    repo_root = Path(__file__).parent.parent.parent
    candidates.append(repo_root / "project.json")

    # Try to load from candidates
    for path in candidates:
        if path.is_file():
            try:
                config = json.loads(path.read_text(encoding="utf-8"))
                return ProjectConfig(config)
            except Exception as e:
                # Log but continue to next candidate
                print(f"Warning: Failed to load project config from {path}: {e}")

    # 4. Default to Octavia for backward compatibility
    default_config = {
        "project": {
            "name": "octavia",
            "slug": "octavia",
            "launchpad": "octavia",
            "repos": [
                "openstack/octavia",
                "openstack/octavia-lib",
                "openstack/octavia-tempest-plugin",
                "openstack/python-octaviaclient"
            ],
            "devstack_services": [
                "devstack@o-api.service",
                "devstack@o-cw.service",
                "devstack@o-hm.service"
            ]
        }
    }
    return ProjectConfig(default_config)


# Global singleton - loaded once when module is imported
PROJECT = load_project_config()


def get_project() -> ProjectConfig:
    """Get the current project configuration.

    Returns:
        ProjectConfig instance (singleton).
    """
    return PROJECT


def reload_project_config() -> ProjectConfig:
    """Reload project configuration from disk.

    Useful for tests or when config file changes at runtime.

    Returns:
        Newly loaded ProjectConfig instance.
    """
    global PROJECT
    PROJECT = load_project_config()
    return PROJECT
