#!/usr/bin/env python3

import sys
import shlex

from time import sleep

# My utilities
import utils

# Entry point
if __name__ == "__main__":
    try:
        if len(sys.argv) <= 3:
            utils.bail("Usage: {} <root> <snapshot> <package> [<package> ...]".format(sys.argv[0]))

        # Parse args and snapshot
        root = sys.argv[1] if sys.argv[1].endswith("/") else (sys.argv[1] + "/")
        snap = root + sys.argv[2].strip("/").replace("/", ".").strip("/")
        utils.call(shlex.split("btrfs sub snap {} {}".format(root, snap)), exceptions=True, combine=True, log=True)

        # Grab rest and spawn build container
        packages = set(sys.argv[3:])
        utils.call(shlex.split("systemd-nspawn -D {0} --bind={1} /usr/bin/env PKGDEST={1}/{2} {1}/build.py".format(snap, "/opt/aur-builder", "repo")) + list(packages), exceptions=True, combine=True, log=True)
    except utils.CallException as e:
        utils.dumperror(e)
        #raise
    except Exception as e:
        print("Caught exception:")
        print(e.args)
        snap = None
        exit(1)
    else:
        exit(0)
    finally:
        # Clean snapshot until success
        code = 1
        while snap and code and not code in [11, 12]:
            code = utils.call(shlex.split("btrfs sub del {}".format(snap)), combine=True, log=True)[2]
            sleep(2)
