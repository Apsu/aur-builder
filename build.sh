#!/bin/bash

# Grab args from params or stdin
args=("$@")
[[ $# -gt 0 ]] || read -t 0.1 -a args
[[ ${#args[@]} -gt 0 ]] || { echo "No packages specified. Bailing!"; exit 0; }

# Need a place to put packages
[[ -v PKGDEST ]] || { echo "PKGDEST must be provided. Bailing!"; exit 0; }

#Handle errors
set -e
error() { echo "Trapped an error. Bailing!"; }
trap error ERR

# Vars and whatnot
commonopts="--needed --noconfirm --noprogressbar"
depopts="--asdeps"
guard=0

# Build loop
build() {
  ((guard++ > 5)) && { echo "Inception level 5 reached. Bailing!"; exit 0; }

  # Grab package dep chains
  makedeps=($(cower -ii --format %M --listdelim='\n' "$@"))
  rundeps=($(cower -ii --format %D --listdelim='\n' "$@"))

  # Filter usefully
  repomakedeps=($(IFS=\|; expac -Ss %n "^(${makedeps[*]})$" | sort -u))
  repormdeps=($(echo "${repomakedeps[@]}" "${repormdeps[@]}" | sort -u ))
  aurmakedeps=($(cower -ii --format %n --listdelim='\n' "${makedeps[@]}" | sort -u))
  aurrmdeps=($(echo "${aurmakedeps[@]}" "${aurrmdeps[@]}" | sort -u ))
  aurrundeps=($(cower -ii --format %n --listdelim='\n' "${rundeps[@]}" | sort -u))

  # Install binary makedeps
  [[ ${#repomakedeps[@]} -gt 0 ]] && {
    echo "Installing repo makedeps: ${repomakedeps[*]}"
    pacman -S $commonopts $depopts "${repomakedeps[@]}"
  }

  # Build/Install AUR makedeps
  [[ ${#aurmakedeps[@]} -gt 0 ]] && {
    echo "Installing AUR makedeps: ${aurmakedeps[*]}"
    for package in "${aurmakedeps[@]}"
    do
      cower -d $package
      pushd $package
      makepkg -sri $commonopts $depopts --asroot
      popd
      rm -rf $package
    done
  }

  # Build specified AUR packages
  echo "Building specified AUR packages: $*"
  for package in "$@"
  do
    cower -d $package
    pushd $package
    makepkg $commonopts --nodeps --asroot --sign || true # Any of these can fail
    popd
    rm -rf $package
  done

  # .. and recurse for unspecified AUR deps
  [[ ${#aurrundeps[@]} -gt 0 ]] && {
    echo "Recursing for unspecified runtime AUR deps: ${aurrundeps[*]}"
    build "${aurrundeps[@]}"
  }

  # Remove AUR makedeps
  [[ ${#repormdeps[@]} -gt 0 ]] || [[ ${#aurrmdeps[@]} -gt 0 ]] && {
    echo "Removing makedeps we installed: ${repormdeps[*]} ${aurrmdeps[*]}"
    pacman -Runs $commonopts "${repormdeps[@]}" "${aurrmdeps[@]}"
  }
}

# Do the needful!
mkdir -p build; cd build
build "${args[@]}"
