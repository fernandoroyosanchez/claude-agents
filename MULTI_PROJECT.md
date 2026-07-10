# Multi-Project Support

Claude Agents can now monitor **any OpenStack project**, not just Octavia.

## Quick Start

### For OVN-Octavia-Provider

```bash
# 1. Copy the OVN example config
cp project.ovn-octavia.json project.json

# 2. Install agents (they auto-detect the project)
./setup-agents.sh

# 3. Commands are now OVN-specific:
ovn-openstack-triage-bugs
ovn-openstack-review-agent
ovn-openstack-ci-agent
```

**Output locations:**
- Bug triages: `~/ovn-octavia_bug_triages/`
- Reviews: `~/ovn-octavia_reviews/`
- CI failures: `~/ovn-octavia_ci_failures/`

**Launchpad:** Bugs fetched from `neutron` project

**Repos monitored:**
- `openstack/networking-ovn`
- `openstack/ovn-octavia-provider`

---

### For Other Projects

Create `project.json`:

```json
{
  "project": {
    "name": "neutron",
    "slug": "neutron",
    "launchpad": "neutron",
    "repos": [
      "openstack/neutron",
      "openstack/neutron-lib"
    ],
    "devstack_services": [
      "devstack@q-svc.service",
      "devstack@q-agt.service"
    ]
  }
}
```

Then run:

```bash
./setup-agents.sh
```

CLI commands: `neutron-triage-bugs`, `neutron-review-agent`, etc.

---

## Configuration Priority

Settings are applied in this order (later wins):

1. **Global project defaults** (`project.json`)
2. **Agent config file** (`<agent>/config.json`)
3. **Environment variables** (e.g., `LAUNCHPAD_PROJECT=nova`)

### Example Priority Flow

With `project.json`:
```json
{
  "project": {
    "launchpad": "neutron",
    "triages_dir": "~/ovn-octavia_bug_triages"
  }
}
```

And `bug-triage-agent/config.json`:
```json
{
  "launchpad_project": "octavia"  
}
```

**Result:** Uses `octavia` (agent config wins)

If you delete `bug-triage-agent/config.json`:

**Result:** Uses `neutron` (project.json default)

---

## Config File Locations

Project config is loaded from (first found wins):

1. `$CLAUDE_AGENTS_PROJECT_CONFIG` env var
2. `~/.config/claude-agents/project.json`
3. `<repo-root>/project.json`
4. **Default:** Octavia (backward compatibility)

**Recommendation:** Use `<repo-root>/project.json` for per-repo projects, or `~/.config/claude-agents/project.json` for system-wide default.

---

## Fields Reference

### Required

- **name**: Full project name (e.g., `"ovn-octavia-provider"`)

### Optional

- **slug**: Filesystem identifier (default: lowercase name with `/` → `-`)
  - Used in: paths, CLI commands, systemd units
  - Example: `ovn-octavia` → `~/ovn-octavia_bug_triages/`

- **launchpad**: Launchpad project ID (default: same as slug)
  - Example: OVN uses `neutron` Launchpad project

- **repos**: List of `org/repo` to monitor (default: `["openstack/{name}"]`)

- **devstack_services**: List of systemd service names for health checks
  - Example: `["devstack@q-ovn-metadata-agent.service"]`
  - Leave empty `[]` if no DevStack services

### Path Overrides (rarely needed)

You can override default paths if needed:

```json
{
  "project": {
    "name": "nova",
    "triages_dir": "/custom/path/nova_triages",
    "triage_tracking_file": "/custom/tracking.json"
  }
}
```

All paths support `~` expansion.

---

## Migration from Octavia-Only

### Before (hardcoded Octavia):

```bash
openstack-triage-bugs
# Always uses Launchpad octavia project
# Always outputs to ~/octavia_bug_triages/
```

### After (project-agnostic):

**Option 1: Keep using Octavia** (no changes needed)

```bash
# No project.json → defaults to Octavia
openstack-triage-bugs  # Still works!
```

**Option 2: Switch to OVN**

```bash
cp project.ovn-octavia.json project.json
./setup-agents.sh

ovn-openstack-triage-bugs
# Uses Launchpad neutron project
# Outputs to ~/ovn-octavia_bug_triages/
```

---

## CLI Command Naming

Commands follow the pattern: `{slug}-<agent>-<action>`

**Examples:**

| Project | Slug | Triage Command | Review Command |
|---------|------|----------------|----------------|
| octavia | `octavia` | `openstack-triage-bugs` | `openstack-review-agent` |
| ovn-octavia-provider | `ovn-octavia` | `ovn-openstack-triage-bugs` | `ovn-openstack-review-agent` |
| neutron | `neutron` | `neutron-triage-bugs` | `neutron-review-agent` |
| nova | `nova` | `nova-triage-bugs` | `nova-review-agent` |

---

## Systemd Unit Naming

Units follow the pattern: `{slug}-<agent>.service` / `{slug}-<agent>.timer`

**Examples:**

```bash
# Octavia
systemctl --user enable openstack-bug-triage.timer

# OVN-Octavia
systemctl --user enable ovn-openstack-bug-triage.timer

# Neutron
systemctl --user enable neutron-bug-triage.timer
```

---

## Testing Your Configuration

```bash
# Test that project config loads correctly
python3 -c "
from agents_lib import PROJECT
print(f'Project: {PROJECT.name}')
print(f'Slug: {PROJECT.slug}')
print(f'Launchpad: {PROJECT.launchpad}')
print(f'Repos: {PROJECT.repos}')
print(f'Triages dir: {PROJECT.triages_dir}')
"

# Test an agent config
cd bug-triage-agent
python3 config.py
```

---

## Examples

### Example 1: Pure OVN Setup

```bash
# project.json
{
  "project": {
    "name": "ovn-octavia-provider",
    "slug": "ovn-octavia",
    "launchpad": "neutron",
    "repos": [
      "openstack/networking-ovn",
      "openstack/ovn-octavia-provider"
    ]
  }
}

# No per-agent configs needed - uses project.json
./setup-agents.sh

ovn-openstack-triage-bugs
ovn-openstack-review-agent
ovn-openstack-ci-agent
```

### Example 2: Mixed (Global OVN + Per-Agent Override)

```bash
# project.json (global default)
{
  "project": {
    "name": "ovn-octavia-provider",
    "launchpad": "neutron"
  }
}

# bug-triage-agent/config.json (override just for triage)
{
  "launchpad_project": "octavia",  # Triage Octavia bugs instead
  "triages_output_dir": "~/custom_octavia_triages"
}

# Result:
# - Bug triage → Octavia bugs
# - Code review → OVN repos (from project.json)
# - CI failures → OVN repos (from project.json)
```

---

## Troubleshooting

### Problem: Commands not found

```bash
# Check if setup script was run after creating project.json
./setup-agents.sh

# Verify commands were installed
which ovn-openstack-triage-bugs
```

### Problem: Still using Octavia defaults

```bash
# Check project config is being loaded
python3 -c "from agents_lib import PROJECT; print(PROJECT.name)"

# If still shows "octavia":
# 1. Create project.json in repo root
# 2. OR set CLAUDE_AGENTS_PROJECT_CONFIG=/path/to/config.json
# 3. OR create ~/.config/claude-agents/project.json
```

### Problem: Mixing projects accidentally

Each repo should have its own `project.json`. Don't mix OVN and Octavia in the same repo unless you specifically want per-agent overrides.

---

## Advanced: Supporting Multiple Projects Simultaneously

If you want to monitor **both** Octavia and OVN from the same machine:

**Option 1: Two Repos** (Recommended)

```bash
~/claude-agents-octavia/
  project.json  # octavia config
  # Run: ./setup-agents.sh

~/claude-agents-ovn/
  project.json  # ovn-octavia config
  # Run: ./setup-agents.sh

# Result:
# - openstack-triage-bugs (from first repo)
# - ovn-openstack-triage-bugs (from second repo)
# - Both can run simultaneously with different systemd units
```

**Option 2: Single Repo with User Config**

```bash
# Set default in ~/.config/claude-agents/project.json
{
  "project": {
    "name": "ovn-octavia-provider"
  }
}

# Override per agent via config.json
bug-triage-agent/config.json:
{
  "launchpad_project": "neutron"  # OVN bugs
}

code-review-agent/config.json:
{
  "repositories": ["openstack/octavia"]  # Octavia reviews
}
```

This is more complex but allows mixing projects in one installation.

---

## Backward Compatibility

All existing Octavia-specific installations continue to work without changes:

- ✅ No `project.json` → defaults to Octavia
- ✅ Existing `config.json` files take precedence
- ✅ CLI commands updated to `openstack-*`
- ✅ Systemd units updated to `openstack-*.service`

**Migration is opt-in:** create `project.json` only when ready.
