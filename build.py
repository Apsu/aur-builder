#!/usr/bin/env python3

import os
import sys
import shlex

# My utilities
import utils

# Main build loop
def build(packages=set(), repomakedeps=set(), aurmakedeps=set(), guard=0, env={}):
    if guard > 5:
        utils.bail("Inception level 5 reached. Bailing!")

    # Useful options
    commonopts = shlex.split("--noconfirm --noprogressbar")
    asdepsopts = shlex.split("--needed --asdeps")
    asrootopts = shlex.split("--asroot")
    makepkgopts = commonopts + asrootopts + shlex.split("--nodeps --sign")
    allopts = commonopts + asdepsopts + asrootopts

    # Query and filter
    rundeps = utils.call(shlex.split("cower -qii --format %D") + list(packages), sets=True)[0]
    makedeps = utils.call(shlex.split("cower -qii --format %M") + list(packages), sets=True)[0]
    aurrundeps = utils.call(shlex.split("cower -qii --format %n") + list(rundeps), sets=True)[0]
    aurmakedeps |= utils.call(shlex.split("cower -qii --format %n") + list(makedeps), sets=True)[0]
    repomakedeps |= utils.call(shlex.split("expac -Ss %n") + ["^(" + "|".join(makedeps) + ")$"], sets=True)[0]

    try:
        # Add repo deps
        if repomakedeps:
            print("Installing repo makedeps:", " ".join(repomakedeps))
            utils.call(shlex.split("pacman -S") + commonopts + asdepsopts + list(repomakedeps), exceptions=True, log=True)

        # Makepkg loops
        if aurmakedeps:
            print("Installing AUR build deps:", " ".join(aurmakedeps))
            for package in aurmakedeps:
                utils.call(shlex.split("cower -d") + [package], exceptions=True, log=True)
                utils.call(shlex.split("makepkg -sri") + allopts + [package], exceptions=True, log=True, cwd=package, env=env)
                #utils.call(shlex.split("rm -rf") + [package], exceptions=True)

        print("Building explicit AUR packages:", " ".join(packages))
        for package in packages:
            try:
                utils.call(shlex.split("cower -d") + [package], exceptions=True, log=True)
                utils.call(shlex.split("makepkg") + makepkgopts + [package], exceptions=True, log=True, cwd=package, env=env)
            except CallException as e:
                print("Error building package {}:".format(package))
                utils.dumperror(e)
                continue

        # Handle implicit AUR deps
        if aurrundeps:
            print("Recursing for implicit AUR runtime deps:", " ".join(aurrundeps))
            build(aurrundeps, repomakedeps, aurmakedeps, guard+1, env)
    except utils.CallException as e:
        utils.dumperror(e)
        raise
    finally:
        # Remove repo deps
        if repomakedeps:
            print("Removing repo makedeps:", " ".join(repomakedeps))
            utils.call(shlex.split("pacman -Runs") + commonopts + list(repomakedeps), exceptions=True, log=True)

# Entry point
if __name__ == "__main__":
    try:
        if len(sys.argv) <= 1:
            utils.bail("Usage: {} <package> [<package> ...]".format(sys.argv[0]))

        # Build
        print("Environment:", os.environ)
        build(set(sys.argv[1:]), env=os.environ)
    except Exception as e:
        print("Caught exception:")
        print(e.args)
        exit(1)
    else:
        exit(0)
