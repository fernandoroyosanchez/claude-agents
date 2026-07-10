# Testing Guide - Multi-Project Installation

Quick guide for testing the multi-project setup in an isolated Docker container.

## Prerequisites

- Docker installed and running
- This repository cloned locally

## Quick Test

```bash
# 1. Navigate to repo
cd ~/Documentos/gitprojects/claude-agents

# 2. Run test environment
./test-in-docker.sh

# 3. Inside container - test with OVN
cp project.ovn-octavia.json project.json
./setup-agents.sh --no-systemd --no-notifications bug-triage

# 4. Verify
ls ~/.venv/claude-agents/bin/ | grep ovn-octavia

# Expected output:
# ovn-octavia-triage-bugs

# 5. Test config
python3 -c "
import sys
sys.path.insert(0, 'bug-triage-agent')
from config import load_config
cfg = load_config()
print(f'✓ Launchpad: {cfg[\"launchpad_project\"]}')  # Should be: neutron
print(f'✓ Output: {cfg[\"triages_output_dir\"]}')    # Should contain: ovn-octavia
print(f'✓ Repos: {cfg[\"search_repos\"][:2]}')        # Should include: networking-ovn
"
```

## Expected Results

### OVN-Octavia Configuration

When using `project.ovn-octavia.json`:

- **CLI Commands:** `ovn-octavia-*`
- **Launchpad Project:** `neutron` (not octavia!)
- **Output Dirs:** `~/ovn-octavia_bug_triages/`, etc.
- **Repos:** `openstack/networking-ovn`, `openstack/ovn-octavia-provider`

### Octavia Configuration (Default)

When using `project.sample.json`:

- **CLI Commands:** `openstack-*`
- **Launchpad Project:** `octavia`
- **Output Dirs:** `~/octavia_bug_triages/`, etc.
- **Repos:** `openstack/octavia`, `openstack/octavia-lib`, etc.

## Full Test Suite

```bash
./test-in-docker.sh

# Inside container:

# Test 1: OVN Installation
cp project.ovn-octavia.json project.json
./setup-agents.sh --no-systemd --no-notifications bug-triage code-review ci-failure

# Verify OVN commands
commands=$(ls ~/.venv/claude-agents/bin/ | grep ovn-octavia | wc -l)
echo "✓ Generated $commands OVN commands"

# Test 2: Octavia Installation  
cp project.sample.json project.json
./setup-agents.sh --update --no-systemd --no-notifications bug-triage

# Verify Octavia commands
commands=$(ls ~/.venv/claude-agents/bin/ | grep "^openstack-" | wc -l)
echo "✓ Generated $commands Octavia commands"

# Test 3: Custom Project
cat > project.json << 'CUSTOM'
{
  "project": {
    "name": "nova",
    "slug": "nova",
    "launchpad": "nova",
    "repos": ["openstack/nova"]
  }
}
CUSTOM

./setup-agents.sh --update --no-systemd --no-notifications bug-triage

# Verify Nova commands
ls ~/.venv/claude-agents/bin/ | grep nova

# Exit container
exit
```

## Troubleshooting

### Problem: Docker not found

```bash
# Install Docker (Ubuntu/Debian)
sudo apt-get install docker.io
sudo usermod -aG docker $USER
# Log out and back in
```

### Problem: Permission denied

```bash
# Make sure user is in docker group
groups | grep docker

# If not, add and re-login
sudo usermod -aG docker $USER
```

### Problem: Build fails

```bash
# Clean and rebuild
docker rmi claude-agents-test
./test-in-docker.sh
```

## What Gets Tested

- ✅ Project config detection
- ✅ Dynamic CLI command generation
- ✅ Correct slug usage in commands
- ✅ Agent config loading with PROJECT defaults
- ✅ Multiple project configs in one venv
- ✅ Switching between projects
- ✅ Backward compatibility (Octavia default)

## Notes

- The repo is mounted **read-only** in Docker
- No changes are made to your host machine
- The venv is created inside the container only
- Each `./test-in-docker.sh` run starts fresh
- Perfect for testing without side effects
