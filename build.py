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
def build(args=set(), repomakedeps=set(), aurmakedeps=set(), guard=0):
    if guard > 5:
        bail("Inception level 5 reached. Bailing!")

    # Useful options
    commonopts = shlex.split("--noconfirm --noprogressbar")
    asdepsopts = shlex.split("--needed --asdeps ")
    asrootopts = shlex.split("--asroot")

    # Query and filter
    makedeps = callset(shlex.split("cower -qii --format %M") + list(args))[0]
    rundeps = callset(shlex.split("cower -qii --format %D") + list(args))[0]
    repomakedeps |= callset(shlex.split("expac -Ss %n") + ["^(" + "|".join(makedeps) + ")$"])[0]
    aurmakedeps |= callset(shlex.split("cower -qii --format %n") + list(makedeps))[0]

    if repomakedeps:
        print("Installing repo makedeps:", " ".join(repomakedeps))
        stderr = call(shlex.split("pacman -S") + commonopts + asdepsopts + list(repomakedeps))[1]
        if stderr:
            print("Errors:", stderr)

    if repomakedeps:
        print("Removing repo makedeps:", " ".join(repomakedeps))
        stderr = call(shlex.split("pacman -Runs") + commonopts + list(repomakedeps))[1]
        if stderr:
            print("Errors:", stderr)

    #build(args, repomakedeps, aurmakedeps, guard+1)

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
