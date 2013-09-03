#!/usr/bin/env python3

import re
import sys
import shlex
import subprocess

from time import sleep
from Namcap import package

# Easier exit paths
def bail(msg):
    raise Exception(msg)

def call(cmd, **kwargs):
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, **kwargs) as process:
        return process.communicate() + (process.returncode, )

def callset(cmd, **kwargs):
    stdout, stderr, code = call(cmd, **kwargs)
    return set(stdout.split()) if stdout else set(), set(stderr.split()) if stderr else set(), code

# Main build loop
def build(packages=set(), repomakedeps=set(), aurmakedeps=set(), guard=0):
    if guard > 5:
        bail("Inception level 5 reached. Bailing!")

    # Useful options
    commonopts = shlex.split("--noconfirm --noprogressbar")
    asdepsopts = shlex.split("--needed --asdeps")
    asrootopts = shlex.split("--asroot")
    makepkgopts = commonopts + asrootopts + shlex.split("--nodeps --sign")
    allopts = commonopts + asdepsopts + asrootopts

    # Query and filter
    makedeps = callset(shlex.split("cower -qii --format %M") + list(packages))[0]
    rundeps = callset(shlex.split("cower -qii --format %D") + list(packages))[0]
    aurmakedeps |= callset(shlex.split("cower -qii --format %n") + list(makedeps))[0]
    aurrundeps = callset(shlex.split("cower -qii --format %n") + list(rundeps))[0]
    repomakedeps |= callset(shlex.split("expac -Ss %n") + ["^(" + "|".join(makedeps) + ")$"])[0]

    # Add repo deps
    if repomakedeps:
        print("Installing repo makedeps:", " ".join(repomakedeps))
        stderr = call(shlex.split("pacman -S") + commonopts + asdepsopts + list(repomakedeps))[1]
        if stderr:
            print("Errors:", stderr)

    # Makepkg loops
    if aurmakedeps:
        print("Installing AUR build deps:", " ".join(aurmakedeps))
        for package in aurmakedeps:
            stderr, code = call(shlex.split("cower -d") + [package])[1:3]
            if not code:
                bail("Error building package: {}".format(stderr))
            stderr, code = call(shlex.split("makepkg -sri") + allopts + [package])[1:3]
            if not code:
                bail("Error building package: {}".format(stderr))

    print("Building explicit AUR packages:", " ".join(packages))
    for package in packages:
        stderr, code = call(shlex.split("cower -d") + [package])[1:3]
        if not code:
            print("Error building package:", package)
            continue
        stderr, code = call(shlex.split("makepkg") + makepkgopts + [package])[1:3]
        if not code:
            print("Error building package:", package)
            continue

    # Remove repo deps
    if repomakedeps:
        print("Removing repo makedeps:", " ".join(repomakedeps))
        stderr = call(shlex.split("pacman -Runs") + commonopts + list(repomakedeps))[1]
        if stderr:
            print("Errors:", stderr)

    # Handle implicit AUR deps
    if aurrundeps:
        print("Recursing for implicit AUR runtime deps:", " ".join(aurrundeps))
        build(aurrundeps, repomakedeps, aurmakedeps, guard+1)

# Entry point
if __name__ == "__main__":
    try:
        if len(sys.argv) <= 3:
            bail("Usage: {} <root> <snapshot> <package> [<package> ...]".format(sys.argv[0]))

        # Parse args and snapshot
        root = sys.argv[1] if sys.argv[1].endswith("/") else (sys.argv[1] + "/")
        snap = root + sys.argv[2].strip("/").replace("/",".").strip("/")
        cmd=shlex.split("btrfs sub snap {} {}".format(root, snap))
        #subprocess.check_call(cmd)

        # Grab rest and build
        args = set(sys.argv[3:])
        build(args)
    except Exception as e:
        #print(e)
        raise
    finally:
        try:
            # Clean snapshot until success
            cmd=shlex.split("btrfs sub del {}".format(snap))
            #while subprocess.call(cmd):
            #    sleep(2)
        # Catch inception
        except:
            pass
