#!/bin/sh
# Test-env helper: import a locally built image into each host's containerd cache.
# The three-cluster test env resolves xnet.registry.io to its own Harbor (10.2.5.85),
# which we cannot push to, so images are side-loaded; manifests then use IfNotPresent.
# Usage: deploy-edge/load_image.sh IMAGE HOST...   (SSH as root; uses $SSHPASS when set)
set -eu
image=$1; shift
ssh_cmd="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
if [ -n "${SSHPASS:-}" ]; then ssh_cmd="sshpass -e $ssh_cmd"; fi
for host in "$@"; do
  echo "loading $image -> $host"
  docker save "$image" | $ssh_cmd "root@$host" 'ctr -n k8s.io images import - >/dev/null && ctr -n k8s.io images ls -q | grep -c "'"$image"'"'
done
