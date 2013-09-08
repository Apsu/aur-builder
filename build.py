#!/usr/bin/env python3

import os
import sys
import shlex
import argparse

# Ordered sets
from ordered_set import OrderedSet

# My utilities
import utils

# Main build loop
def build(packages, env={}, quiet=False):
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
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Build script for AUR packages", add_help=True)
    parser.add_argument("-q", "--quiet", action="store_true", help="minimize output (default: %(default)s)")
    parser.add_argument("-e", "--env", action="append", help="minimize output (default: %(default)s)")
    parser.add_argument("packages", metavar="package", nargs="+", help="AUR package(s) to build")

    # Parse args
    args = parser.parse_args()

    try:
        # Reformat env vars
        os.environ.update(dict(map(lambda s: s.split("="), args.env)))

        # cd somewhere out of /
        if "HOME" in os.environ:
            os.chdir(os.environ["HOME"])
        else:
            os.chdir("/opt")

        print(os.environ)
        build(set(args.packages), env=os.environ, quiet=args.quiet)
    except Exception as e:
        print("Caught exception:", e)
        exit(1)
    else:
        exit(0)
