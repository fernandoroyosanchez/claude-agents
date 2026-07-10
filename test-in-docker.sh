#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  Claude Agents - Docker Test Environment"
echo "=========================================="
echo ""

# Build the test image
echo "Building test Docker image..."
docker build -f Dockerfile.test -t claude-agents-test .
echo ""

# Run the container
echo "Starting test container..."
echo "The repository is mounted at /workspace"
echo ""
echo "Quick test commands:"
echo "  cp project.ovn-octavia.json project.json"
echo "  ./setup-agents.sh --no-systemd --no-notifications bug-triage"
echo "  ls ~/.venv/claude-agents/bin/ | grep ovn-octavia"
echo ""
echo "=========================================="
echo ""

# Check if gcloud credentials exist
if [ ! -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    echo "⚠️  WARNING: No Google Cloud credentials found."
    echo "   Run 'gcloud auth application-default login' to authenticate"
    echo "   Container will start but Claude Agent SDK won't work without credentials"
    echo ""
fi

# Get GCP project ID
GCP_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$GCP_PROJECT" ]; then
    echo "⚠️  WARNING: No GCP project configured."
    echo "   Run 'gcloud config set project YOUR_PROJECT_ID' to configure"
    echo ""
fi

docker run -it --rm \
    --privileged \
    -v "$SCRIPT_DIR:/workspace:Z" \
    -v "$HOME/.config/gcloud:/root/.config/gcloud:Z" \
    -e CLAUDE_CODE_USE_VERTEX=1 \
    -e GOOGLE_CLOUD_PROJECT="$GCP_PROJECT" \
    -e VERTEX_AI_PROJECT="$GCP_PROJECT" \
    -w /workspace \
    claude-agents-test \
    /bin/bash
