#!/usr/bin/env bash
# usage: scripts/pod-install.sh <target-repo> [--with-sample] [--vendor-plugins] [--force]
# Installs the pod kit core into an existing git repo. Never overwrites Makefile, AGENTS.md
# or CLAUDE.md; other existing files are skipped unless --force. Safe to run again. No network.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/pod_install.py" "$@"
