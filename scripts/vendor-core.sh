#!/usr/bin/env bash
# Refresh plugin/agent_sandbox_backend/_vendor/agent_sandbox/core.py from a self-hosted-agent-sandbox tag.
set -euo pipefail
TAG=${1:?usage: scripts/vendor-core.sh <tag>}
cd "$(dirname "$0")/.."
DST=plugin/agent_sandbox_backend/_vendor
curl -fsSL "https://raw.githubusercontent.com/xiaoyaner0201/self-hosted-agent-sandbox/$TAG/src/agent_sandbox/core.py" -o "$DST/agent_sandbox/core.py"
BLOB=$(git hash-object "$DST/agent_sandbox/core.py")
sed -i.bak -e "s|^- source tag: .*|- source tag: $TAG|" -e "s|^- git blob sha1: .*|- git blob sha1: $BLOB|" "$DST/VENDORED.md"
rm -f "$DST/VENDORED.md.bak"
echo "vendored $TAG ($BLOB)"
