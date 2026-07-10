# Testing in an Isolated Environment

This guide shows how to test the multi-project setup in an isolated environment (Docker or Vagrant) without affecting your local machine.

## Option 1: Docker (Recommended - Faster)

### Quick Start

```bash
cd ~/Documentos/gitprojects/claude-agents

# Build and run test container (interactive)
./test-in-docker.sh
```

Inside the container:

```bash
# Already in /home/tester/claude-agents

# Copy OVN config
cp project.ovn-octavia.json project.json

# Run setup
./setup-agents.sh --no-systemd --no-notifications

# Verify installation
ls ~/.venv/claude-agents/bin/ | grep ovn-octavia

# Test config loading
python3 -c "from agents_lib import PROJECT; print(f'Project: {PROJECT.name}, Slug: {PROJECT.slug}, Launchpad: {PROJECT.launchpad}')"
```

### Manual Docker Commands

```bash
# Build image
docker build -f Dockerfile.test -t claude-agents-test .

# Run container (mounts repo read-only)
docker run -it --rm \
    -v "$PWD:/home/tester/claude-agents:ro" \
    -w /home/tester/claude-agents \
    claude-agents-test \
    /bin/bash
```

### Clean Up

```bash
# Remove test image
docker rmi claude-agents-test
```

## Option 2: Vagrant (Full VM)

### Quick Start

### 1. Start the Test VM

```bash
cd ~/Documentos/gitprojects/claude-agents

# Start and provision the VM (first time takes ~5 minutes)
vagrant up

# SSH into the VM
vagrant ssh
```

### 2. Inside the VM - Test OVN Setup

```bash
# Navigate to the synced repo
cd claude-agents

# Copy OVN config
cp project.ovn-octavia.json project.json

# Run setup (selects OVN automatically since project.json exists)
./setup-agents.sh --no-systemd --no-notifications

# The setup will:
# - Detect project.json (OVN config)
# - Create venv at ~/.venv/claude-agents
# - Install all agents
# - Generate CLI commands: ovn-octavia-*
```

### 3. Verify Installation

```bash
# Check generated commands
ls ~/.venv/claude-agents/bin/ | grep ovn-octavia

# Should show:
# ovn-openstack-triage-bugs
# ovn-openstack-review-agent
# ovn-openstack-review-change
# ovn-openstack-ci-agent
# ovn-openstack-analyze-ci
# ovn-openstack-reproduce-bugs
# ovn-openstack-devstack-test
# ovn-openstack-jira-triage
# ovn-openstack-propose-fix
# ovn-openstack-verify-fix

# Activate venv
source ~/.venv/claude-agents/bin/activate

# Test a command
which ovn-openstack-triage-bugs

# Verify project config
python3 -c "from agents_lib import PROJECT; print(f'Project: {PROJECT.name}'); print(f'Slug: {PROJECT.slug}'); print(f'Launchpad: {PROJECT.launchpad}')"

# Should print:
# Project: ovn-octavia-provider
# Slug: ovn-octavia
# Launchpad: neutron
```

### 4. Test Agent Config Loading

```bash
cd claude-agents

# Test bug triage config
python3 -c "
import sys
sys.path.insert(0, 'bug-triage-agent')
from config import load_config
cfg = load_config()
print(f'Launchpad project: {cfg[\"launchpad_project\"]}')
print(f'Output dir: {cfg[\"triages_output_dir\"]}')
print(f'Repos: {cfg[\"search_repos\"]}')
"

# Should print:
# Launchpad project: neutron
# Output dir: /home/vagrant/ovn-octavia_bug_triages
# Repos: ['openstack/networking-ovn', 'openstack/ovn-octavia-provider']
```

### 5. Test Different Project Configs

```bash
# Test with Neutron
cat > project.json << 'EOF'
{
  "project": {
    "name": "neutron",
    "slug": "neutron",
    "launchpad": "neutron",
    "repos": ["openstack/neutron"]
  }
}
EOF

# Reinstall
./setup-agents.sh --update --no-systemd --no-notifications

# New commands available
ls ~/.venv/claude-agents/bin/ | grep neutron
# neutron-triage-bugs
# neutron-review-agent
# ... etc

# Test with Octavia (default)
cp project.sample.json project.json
./setup-agents.sh --update --no-systemd --no-notifications

ls ~/.venv/claude-agents/bin/ | grep octavia
# openstack-triage-bugs
# openstack-review-agent
# ... etc
```

## VM Management

### Stop the VM
```bash
# From host machine
vagrant halt
```

### Restart the VM
```bash
vagrant up
vagrant ssh
```

### Destroy the VM (clean slate)
```bash
vagrant destroy -f
```

### Start fresh
```bash
vagrant destroy -f
vagrant up
vagrant ssh
```

## Troubleshooting

### Problem: Synced folder not working

```bash
# From host, reload VM with forced sync
vagrant reload
```

### Problem: Out of disk space in VM

```bash
# SSH into VM
vagrant ssh

# Check disk usage
df -h

# Clean Python caches
find /home/vagrant/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

### Problem: Need to test with actual Vertex AI

The VM needs credentials:

```bash
# From host, copy credentials to VM
vagrant ssh

# Inside VM, set up credentials
export CLAUDE_CODE_USE_VERTEX=1
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Or use gcloud
gcloud auth application-default login
```

## Testing Checklist

- [ ] VM starts successfully
- [ ] Repo is synced to `/home/vagrant/claude-agents`
- [ ] `./setup-agents.sh` completes without errors
- [ ] Project config (OVN) is detected
- [ ] CLI commands are generated with `ovn-octavia-` prefix
- [ ] Commands are executable and in PATH
- [ ] `PROJECT.slug` matches config
- [ ] Agent configs load with correct defaults
- [ ] Can switch projects and reinstall
- [ ] Multiple project configs can coexist

## VM Specifications

- **OS:** Ubuntu 22.04 LTS
- **RAM:** 2 GB
- **CPUs:** 2
- **Disk:** ~10 GB (virtual)
- **Network:** NAT (can access internet)

## Advanced: Test with Multiple Projects

```bash
vagrant ssh
cd claude-agents

# Install for OVN
cp project.ovn-octavia.json project.json
./setup-agents.sh --no-systemd --no-notifications bug-triage code-review

# Install for Octavia (different commands, same venv)
cp project.sample.json project.json
./setup-agents.sh --update --no-systemd --no-notifications bug-triage code-review

# Both sets of commands now available
ls ~/.venv/claude-agents/bin/ | grep -E "triage|review"
# openstack-triage-bugs
# openstack-review-agent
# ovn-openstack-triage-bugs
# ovn-openstack-review-agent

# Each uses the correct project when run
# (they read project.json at runtime, not install-time)
```

## Notes

- Changes made inside the VM to the synced folder (`/home/vagrant/claude-agents`) are reflected on the host
- The venv is created inside the VM only (`~/.venv/claude-agents`)
- Test outputs (triages, reviews) are created in the VM
- No changes are made to your host machine's Python environment
