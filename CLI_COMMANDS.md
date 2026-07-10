# CLI Command Generation

This document explains how CLI commands are generated dynamically based on the configured project.

## How It Works

When you run `./setup-agents.sh`, the installation process:

1. **Detects/Creates `project.json`** - Your project configuration
2. **Installs agent packages** - Python packages without hardcoded CLI names
3. **Generates CLI wrappers** - Scripts named `{slug}-{agent}` that call the actual agent code

## Example: OVN-Octavia-Provider

With `project.json`:
```json
{
  "project": {
    "name": "ovn-octavia-provider",
    "slug": "ovn-octavia",
    ...
  }
}
```

**Generated commands:**
```
ovn-openstack-triage-bugs
ovn-openstack-review-agent
ovn-openstack-review-change
ovn-openstack-ci-agent
ovn-openstack-analyze-ci
ovn-openstack-reproduce-bugs
ovn-openstack-devstack-test
ovn-openstack-jira-triage
ovn-openstack-propose-fix
ovn-openstack-verify-fix
```

## Example: Octavia (Default)

With no `project.json` or using `project.sample.json`:
```json
{
  "project": {
    "name": "octavia",
    "slug": "octavia",
    ...
  }
}
```

**Generated commands:**
```
openstack-triage-bugs
openstack-review-agent
openstack-review-change
openstack-ci-agent
openstack-analyze-ci
openstack-reproduce-bugs
openstack-devstack-test
openstack-jira-triage
openstack-propose-fix
openstack-verify-fix
```

## Example: Neutron

With `project.json`:
```json
{
  "project": {
    "name": "neutron",
    "slug": "neutron",
    ...
  }
}
```

**Generated commands:**
```
neutron-triage-bugs
neutron-review-agent
neutron-review-change
... etc
```

## Technical Details

### CLI Wrapper Generator

Location: `agents_lib/agents_lib/cli_wrapper.py`

**What it does:**
- Reads `PROJECT.slug` from the global project config
- For each agent, creates a wrapper script: `{slug}-{agent-name}`
- Wrapper calls the actual Python entry point

**Example generated wrapper (`ovn-openstack-triage-bugs`):**
```python
#!/usr/bin/env python3
"""
Auto-generated CLI wrapper for ovn-octavia-provider triage-bugs

This wrapper ensures the correct project context is loaded.
"""
import sys
from bug_triage_agent import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
```

### Agent Configurations

Defined in `cli_wrapper.py`:

```python
{
    'triage-bugs': 'bug_triage_agent:cli_main',
    'review-agent': 'octavia_review_agent:cli_main',
    'review-change': 'review_single_change:cli_main',
    'ci-agent': 'ci_failure_agent:cli_main',
    ... etc
}
```

### Installation Flow

```
setup-agents.sh
    ↓
1. Create/detect project.json
    ↓
2. Install agents_lib (includes cli_wrapper.py)
    ↓
3. Install agent packages (bug-triage-agent, code-review-agent, etc.)
    ↓
4. Call cli_wrapper.generate_cli_wrapper() for each agent
    ↓
5. Wrapper scripts created in venv/bin/
    ↓
6. Commands available: {slug}-*
```

## Re-generating Commands

If you change your project configuration:

```bash
# 1. Update project.json
vim project.json

# 2. Re-run setup (will regenerate wrappers with new slug)
./setup-agents.sh --update
```

**What happens:**
- Old wrappers (e.g., `openstack-*`) remain in `venv/bin/`
- New wrappers (e.g., `ovn-openstack-*`) are created
- You can manually remove old ones:

```bash
rm ~/.venv/claude-agents/bin/openstack-*
```

## Verifying Installed Commands

```bash
# List all installed agent commands
ls ~/.venv/claude-agents/bin/ | grep -E "triage|review|ci-agent"

# Or with the project slug
source ~/.venv/claude-agents/bin/activate
which ovn-openstack-triage-bugs

# Test a command
ovn-openstack-triage-bugs --help
```

## Multiple Projects on One System

If you want to monitor multiple projects simultaneously:

**Option 1: Separate repos (Recommended)**
```bash
~/claude-agents-openstack/
  project.json  # octavia
  ./setup-agents.sh
  # Commands: openstack-*

~/claude-agents-ovn/
  project.json  # ovn-octavia
  ./setup-agents.sh
  # Commands: ovn-openstack-*
```

**Option 2: Shared venv with both sets of wrappers**
```bash
# Install for Octavia
cp project.sample.json project.json
./setup-agents.sh

# Change project and reinstall
cp project.ovn-octavia.json project.json
./setup-agents.sh --update

# Both sets of commands now available:
openstack-triage-bugs
ovn-openstack-triage-bugs
```

## Troubleshooting

### Problem: Commands not found after install

```bash
# Check if wrapper was created
ls ~/.venv/claude-agents/bin/ | grep triage

# If missing, regenerate
./setup-agents.sh --update
```

### Problem: Wrong project slug in commands

```bash
# Check what project is configured
python3 -c "from agents_lib import PROJECT; print(PROJECT.slug)"

# If wrong, update project.json and reinstall
vim project.json
./setup-agents.sh --update
```

### Problem: Old commands still present

```bash
# Remove old wrappers manually
rm ~/.venv/claude-agents/bin/openstack-*

# Or regenerate all
./setup-agents.sh --update
```

## Advanced: Manual Wrapper Generation

```python
from pathlib import Path
from agents_lib.cli_wrapper import generate_cli_wrapper, get_agent_cli_configs

venv_bin = Path.home() / ".venv/claude-agents/bin"

# Generate all wrappers
for agent_name, entry_function in get_agent_cli_configs().items():
    script_path = generate_cli_wrapper(agent_name, entry_function, venv_bin)
    print(f"Created: {script_path}")
```

## Future: Systemd Unit Generation

Currently, systemd units must be configured manually with the correct project slug.

**Planned:** Similar dynamic generation for systemd units:
- `{slug}-bug-triage.service`
- `{slug}-bug-triage.timer`
- etc.

See `MULTI_PROJECT.md` for current manual systemd setup instructions.
