"""
CLI wrapper generator for project-agnostic agent commands.

This module generates wrapper scripts that call the actual agent implementations
with the correct project context. This allows CLI commands to be project-specific
(e.g., ovn-octavia-triage-bugs vs octavia-triage-bugs) without hardcoding them
in setup.py.
"""

from pathlib import Path
import sys


def generate_cli_wrapper(agent_name: str, entry_function: str, install_dir: Path):
    """Generate a CLI wrapper script for an agent.

    Args:
        agent_name: Agent identifier (e.g., 'triage-bugs', 'review-agent')
        entry_function: Python entry point (e.g., 'bug_triage_agent:cli_main')
        install_dir: Directory where wrapper scripts are installed

    Returns:
        Path to the generated wrapper script.
    """
    from .project_config import PROJECT

    # Generate script name with project slug
    script_name = f"{PROJECT.slug}-{agent_name}"
    script_path = install_dir / script_name

    # Python wrapper that calls the actual entry point
    wrapper_content = f'''#!/usr/bin/env python3
"""
Auto-generated CLI wrapper for {PROJECT.name} {agent_name}

This wrapper ensures the correct project context is loaded.
"""
import sys
from {entry_function.split(":")[0]} import {entry_function.split(":")[1]}

if __name__ == "__main__":
    sys.exit({entry_function.split(":")[1]}())
'''

    script_path.write_text(wrapper_content)
    script_path.chmod(0o755)

    return script_path


def install_cli_wrappers(venv_bin: Path, agent_configs: dict):
    """Install all CLI wrapper scripts for configured agents.

    Args:
        venv_bin: Path to venv bin directory
        agent_configs: Dict mapping agent_name -> entry_function
            Example: {
                'triage-bugs': 'bug_triage_agent:cli_main',
                'review-agent': 'octavia_review_agent:cli_main',
            }

    Returns:
        List of installed script paths.
    """
    installed = []
    for agent_name, entry_function in agent_configs.items():
        script_path = generate_cli_wrapper(agent_name, entry_function, venv_bin)
        installed.append(script_path)
        print(f"  ✓ Installed: {script_path.name}")

    return installed


def get_agent_cli_configs():
    """Return the CLI configuration for all agents.

    Returns:
        Dict mapping agent_name -> entry_function for all agents.
    """
    return {
        # Bug Triage Agent
        'triage-bugs': 'bug_triage_agent:cli_main',

        # Code Review Agent
        'review-agent': 'octavia_review_agent:cli_main',
        'review-change': 'review_single_change:cli_main',

        # CI Failure Agent
        'ci-agent': 'ci_failure_agent:cli_main',
        'analyze-ci': 'analyze_ci_failure:cli_main',

        # Bug Reproduction Agent
        'reproduce-bugs': 'bug_reproduction_agent:cli_main',

        # DevStack Test Agent
        'devstack-test': 'devstack_test_agent:cli_main',

        # JIRA Triage Agent
        'jira-triage': 'jira_triage_agent:cli_main',

        # Fix Proposal Agent
        'propose-fix': 'fix_proposal_agent:cli_main',

        # Fix Verification Agent
        'verify-fix': 'fix_verification_agent:cli_main',
    }


if __name__ == "__main__":
    # Test: show what CLI commands would be generated
    from .project_config import PROJECT

    print(f"Project: {PROJECT.name} (slug: {PROJECT.slug})")
    print("\nCLI Commands that would be generated:")
    print("-" * 50)

    for agent_name in get_agent_cli_configs():
        cmd = f"{PROJECT.slug}-{agent_name}"
        print(f"  {cmd}")
