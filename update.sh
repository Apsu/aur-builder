#!/bin/bash

REPO="${REPO:-propter}"
REPODIR="${REPODIR:-$PWD}"
TIMEOUT="${TIMEOUT:-60}"

source creds

# Change to repo
cd "$REPODIR"

# Update the things
update() {
  # Grab new packages if any
  turbolift -I download -s . -c evan-repo --dl-sync

  # Prune list
  # TODO: Write this

  # Update databases
  repo-add -n -s "${REPO}.db.tar.gz" *.xz
  repo-add -n -f -s "${REPO}.files.tar.gz" *.xz

  # Push back up
  turbolift -I tsync -s . -c evan-repo --cdn-enable

  # Wait and repeat
  sleep $TIMEOUT; update
}

# .doit
update
