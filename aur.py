#!/usr/bin/env python3
"""
Arch Linux AUR Builder

Build a list of AUR packages

Usage:
  aur.py [--help] [--version] [--quiet] [--dest=<path>] <packages>...

Arguments:
  <packages>...            Package(s) to build

Options:
  -h --help                Show this message
  -v --version             Show version
  -q --quiet               Minimize output [default: False]
  -d <path> --dest=<path>  Path to package build destination [default: /opt/build/repo]

"""

import os
import sys
import shlex
import argparse

from docopt import docopt
from ordered_set import OrderedSet

# My utilities
import utils

# Main build loop
def build(packages, env={}, quiet=False):
    print("Environment:", env)

    # Useful options
    commonopts = shlex.split("--noconfirm --noprogressbar")
    asdepsopts = shlex.split("--needed --asdeps")
    asrootopts = shlex.split("--asroot")
    makepkgopts = commonopts + asrootopts + shlex.split("--nodeps --sign")
    allopts = commonopts + asdepsopts + asrootopts

    try:
        # Query and filter initial dep sets
        if not quiet:
            print("Getting initial dependency info for:", " ".join(packages))
        pkgdeps = utils.call(shlex.split("cower -ii --format %M%D") + list(packages), exceptions=False, sets=True, pipe=True)[0]
        aurdeps = utils.call(shlex.split("cower -ii --format %n") + list(pkgdeps), exceptions=False, sets=True, pipe=True)[0]
        aurodeps = OrderedSet(aurdeps)
        repodeps = pkgdeps - aurdeps

        # Check for implicit AUR deps we need to build
        while aurdeps:
            if not quiet:
                print("Checking for AUR deps in:", " ".join(aurdeps))
            pkgdeps = utils.call(shlex.split("cower -ii --format %M%D") + list(aurdeps), exceptions=False, sets=True, pipe=True)[0]
            aurdeps = utils.call(shlex.split("cower -ii --format %n") + list(pkgdeps), exceptions=False, sets=True, pipe=True)[0]

            # Check for cyclic dependencies
            if aurdeps & set(aurodeps):
                if not quiet:
                    print("Cyclic dependencies detected!")
                    print("Requested packages:", packages)
                    print("Detected AUR deps:", " ".join(aurodeps))
                    print("Cyclic deps:", " ".join(aurdeps & set(aurodeps)))
                utils.bail("Bailing due to cyclic dependencies.")

            # Add new deps to sets
            aurodeps |= aurdeps
            repodeps |= pkgdeps - aurdeps

        # Add repo deps
        if repodeps:
            if not quiet:
                print("Installing repo deps:", " ".join(repodeps))
            utils.call(shlex.split("pacman -S") + commonopts + asdepsopts + list(repodeps), pipe=quiet)

        # Makepkg loops
        if aurodeps:
            if not quiet:
                print("Building/installing AUR deps:", " ".join(aurodeps))
            utils.call(shlex.split("cower -d") + aurodeps.items, pipe=quiet)

            # Iterate in reverse since dep chain was built forward
            for package in reversed(aurodeps):
                utils.call(shlex.split("makepkg -si") + allopts + [package], pipe=quiet, cwd=package, env=env)

        if not quiet:
            print("Building AUR packages:", " ".join(packages))
        utils.call(shlex.split("cower -d") + list(packages), pipe=quiet)
        for package in packages:
            try:
                # We'll accept any of these failing
                utils.call(shlex.split("makepkg") + makepkgopts + [package], pipe=quiet, cwd=package, env=env)
                # TODO: Keep track of if
            except utils.CallException as e:
                if quiet:
                    utils.dumperror(e)
                else:
                    print("Error building package {}:".format(package))

    except utils.CallException as e:
        if quiet:
            utils.dumperror(e)
        else:
            print("CallException:", e.cmd)

# Entry point
if __name__ == "__main__":
    opts = docopt(__doc__, version="AUR builder 0.5.0")

    try:
        # Parse opts
        dest = os.path.abspath(opts["--dest"])
        quiet = opts["--quiet"]
        packages = set(opts["<packages>"])

        # Set PKGDEST
        os.environ.update({"PKGDEST": dest})

        # Add path for pod2man and similar perl bits
        os.environ.update({"PATH": os.environ["PATH"] + ":/usr/bin/core_perl"})

        # cd out of /
        os.mkdir("/opt/build")
        os.chdir("/opt/build")

        # idempotently mkdir destination
        os.makedirs(dest, exist_ok=True)

        # .doit!
        build(packages, env=os.environ, quiet=quiet)
    except Exception as e:
        print("Caught exception:", e)
        exit(1)
    else:
        exit(0)
