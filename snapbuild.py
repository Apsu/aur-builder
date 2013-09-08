#!/usr/bin/env python3

import os
import sys
import uuid
import shlex
import argparse

# My utilities
import utils

# Entry point
if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Snapshot and spawn build script for packages", add_help=True)
    parser.add_argument("-l", "--log", nargs="?", type=argparse.FileType("w"), default=sys.stdout, help="log output to specified file (default: stdout)")
    parser.add_argument("-r", "--root", nargs="?", default="/opt/buildroot", help="path to btrfs volume for build snapshots (default: %(default)s)")
    parser.add_argument("-s", "--snapshot", nargs="?", default=uuid.uuid4(), help="name to use for build snapshot (default: %(default)s)")
    parser.add_argument("-b", "--bind", nargs="?", default=os.getcwd(), help="path to bind point for build container (default: %(default)s)")
    parser.add_argument("-x", "--builder", nargs="?", default="build.py", help="build script to execute (default: %(default)s)")
    parser.add_argument("-q", "--quiet", action="store_true", help="minimize output (default: %(default)s)")
    parser.add_argument("packages", metavar="package", nargs="+", help="package(s) to build")

    # Parse args, capture any extra
    args, extra = parser.parse_known_args()

    try:
        # Redirect sys.stdout
        sys.stdout = args.log

        # Clean snapshot args and do it
        root = os.path.abspath(args.root)
        snapshot = os.path.join(root, os.path.normpath(str(args.snapshot).replace("/", "-")))
        utils.call(shlex.split("btrfs sub snap {} {}".format(root, snapshot)), pipe=args.quiet)

        # Clean bindpoint and prepare command to execute
        bind = os.path.abspath(args.bind)
        builder = os.path.join(bind, args.builder)

        # Spawn build script
        utils.call(shlex.split("systemd-nspawn -D {} --bind={} {}".format(snapshot, bind, builder)) + (["-q"] if args.quiet else []) + extra + list(args.packages), pipe=args.quiet)
    except utils.CallException as e:
        if args.quiet:
            utils.dumperror(e)
        else:
            print("CallException:", e.cmd)
    except Exception as e:
        print("Caught exception:", e)
        exit(1)
    else:
        exit(0)
    finally:
        utils.call(shlex.split("btrfs sub del {}".format(snapshot)), exceptions=False, pipe=args.quiet)
