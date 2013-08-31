#!/bin/bash

# Setup
[[ -v BASEDIR ]] || { echo "BASEDIR must be provided. Bailing!"; exit 0; }
BINDDIR="${BINDDIR:-/binddir}"
mkdir -p "${BINDDIR}/repo/x86_64"

# Snapshot provided as first positional arg
[[ $# -gt 0 ]] && { SNAPSHOT="$1"; shift; }
SNAPSHOT="${SNAPSHOT:-$(uuidgen -t)}"
btrfs sub snap "$BASEDIR" "${BASEDIR}/$SNAPSHOT"
BUILDROOT="${BASEDIR}/$SNAPSHOT"

# Clean snapshot
cleanup() {
  while ! btrfs sub del "$BUILDROOT"; do sleep 2; done
}
trap cleanup EXIT

# Stop machine and whatnot
term() {
  machinectl terminate $SNAPSHOT
}
trap term TERM

# Read other args as packages or stdin if none
args=("$@")
[[ $# -gt 0 ]] || read -t 0.1 -a args
[[ ${#args[@]} -gt 0 ]] || { echo "No packages specified. Bailing!"; exit 0; }

# Nspawn and do it up
systemd-nspawn -D "$BUILDROOT" --bind="$BINDDIR" /usr/bin/env PKGDEST="${BINDDIR}/repo/x86_64" "${BINDDIR}/build.sh" "${args[@]}"
