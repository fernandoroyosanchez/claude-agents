"""
Configuration management for the bug triage agent.

Loads configuration from config.json or environment variables.
Uses global project configuration as fallback for project-specific settings.
"""
from pathlib import Path
from agents_lib import (
    load_agent_config,
    apply_cutoff_date,
    expand_config_paths,
    expand_context_config,
    PROJECT,
)


def load_config():
    """
    Load configuration from config.json or config.sample.json.

    Uses global project configuration (PROJECT) as fallback for:
    - launchpad_project
    - triages_output_dir
    - triage_tracking_file
    - search_repos

    Environment variables override config file settings:
    - TRIAGES_OUTPUT_DIR: Override triages_output_dir
    - DEVSTACK_PATH: Override devstack_path
    - LAUNCHPAD_PROJECT: Override launchpad_project
    - MAX_BUGS: Override max_bugs_per_run
    - CUTOFF_DATE: Override cutoff_date

    Returns:
        dict: Configuration dictionary
    """
    config_dir = Path(__file__).parent

    # Define environment variable overrides
    env_overrides = {
        "TRIAGES_OUTPUT_DIR": "triages_output_dir",
        "DEVSTACK_PATH": "devstack_path",
        "LAUNCHPAD_PROJECT": "launchpad_project",
        "MAX_BUGS": "max_bugs_per_run",
        "CUTOFF_DATE": "cutoff_date",
        "CLAUDE_MODEL": "model",
    }

    # Load config using shared library with project-aware defaults
    defaults = {
        "model": "claude-sonnet-4-6",
        "launchpad_project": PROJECT.launchpad,
        "launchpad_tags": PROJECT.launchpad_tags,
        "triages_output_dir": PROJECT.triages_dir,
        "triage_tracking_file": PROJECT.triage_tracking_file,
        "search_repos": PROJECT.repos,
        "devstack_path": "/opt/stack",
        "max_bugs_per_run": 5,
        "bug_statuses": ["New", "Confirmed", "Triaged", "In Progress"],
    }
    config = load_agent_config(config_dir, env_overrides, defaults)

    # Apply project-specific defaults if not in config
    if "launchpad_project" not in config or not config.get("launchpad_project"):
        config["launchpad_project"] = PROJECT.launchpad

    if "launchpad_tags" not in config or config.get("launchpad_tags") is None:
        config["launchpad_tags"] = PROJECT.launchpad_tags

    if "triages_output_dir" not in config or not config.get("triages_output_dir"):
        config["triages_output_dir"] = PROJECT.triages_dir

    if "triage_tracking_file" not in config or not config.get("triage_tracking_file"):
        config["triage_tracking_file"] = PROJECT.triage_tracking_file

    if "search_repos" not in config or not config.get("search_repos"):
        config["search_repos"] = PROJECT.repos

    # Apply cutoff date logic (default to 30 days ago)
    config = apply_cutoff_date(config, "cutoff_date", default_days=30)

    # Expand paths
    path_keys = [
        "triages_output_dir",
        "devstack_path",
        "triage_tracking_file",
    ]
    config = expand_config_paths(config, path_keys)

    feedback = config.get("feedback", {})
    config["feedback_enabled"] = feedback.get("post_to_launchpad", False)
    config["feedback_consumer_key_env"] = feedback.get("consumer_key_env", "LAUNCHPAD_CONSUMER_KEY")
    config["feedback_access_token_env"] = feedback.get("access_token_env", "LAUNCHPAD_ACCESS_TOKEN")
    config["feedback_access_token_secret_env"] = feedback.get(
        "access_token_secret_env", "LAUNCHPAD_ACCESS_TOKEN_SECRET"
    )

    config = expand_context_config(config)

    # Add project metadata for reference
    config["_project"] = PROJECT.to_dict()

    return config


if __name__ == "__main__":
    # Test configuration loading
    try:
        cfg = load_config()
        print("✓ Configuration loaded successfully")
        print(f"  - Launchpad project: {cfg['launchpad_project']}")
        print(f"  - Output directory: {cfg['triages_output_dir']}")
        print(f"  - DevStack path: {cfg['devstack_path']}")
        print(f"  - Max bugs per run: {cfg['max_bugs_per_run']}")
        print(f"  - Cutoff date: {cfg['cutoff_date']}")
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        exit(1)
