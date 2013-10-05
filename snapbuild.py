#!/usr/bin/env python3

import os
import sys
import uuid
import shlex

import utils

from docopt import docopt

__doc__ = """
Btrfs snapshot container builderator

Creates a unique (UUID) snapshot of a bootstrapped buildroot then spawns a
builder in it

Usage:
  {0} [--help] [--version] [--quiet] [--log=<file>]
      [--root=<path>] [--bind=<path>] [--dest=<path>]
      <builder> [<args>...]

Options:
  -h --help                Show this message
  -v --version             Show version
  -q --quiet               Minimize output [default: False]
  -l <file> --log=<file>   Log output to specified file
  -r <path> --root=<path>  Path to btrfs volume for build snapshots [default: /opt/buildroot/arch]
  -b <path> --bind=<path>  Path to bind point for build container [default: .]

Parameters:
  <builder>                Builder to use [default: aur]
  <args>...                Arguments to builder

Builders:
  aur                      Arch Linux AUR

See '{0} <builder> --help' for more information on a specific builder

""".format(os.path.basename(sys.argv[0]))

# Entry point
if __name__ == "__main__":
    opts = docopt(__doc__, options_first=True, version="snapbuild 0.3.0")
    print(opts)

    try:
        # Get output opts
        log = opts["--log"]
        quiet = opts["--quiet"]

        # Get snapshot args and clean buildroot
        root = os.path.abspath(opts["--root"])
        snapshot = os.path.join(root, str(uuid.uuid4()))

        # Clean bindpoint and prepare command to execute
        bind = os.path.abspath(opts["--bind"])
        builder = opts["<builder>"]
        build = "{}.py".format(os.path.join(bind, builder))
        args = opts["<args>"]

        # Redirect sys.stdout to logfile
        if log:
            sys.stdout = open(log, "a")

    except OSError as e:
        print("Error opening logfile:", log)
        print("Exception:", e)
        exit(1)
    except Exception as e:
        print("Error parsing args:", args)
        print("Exception:", e)
        exit(2)

    try:
        if not args or "-h" in args:
            utils.call(shlex.split("{} -h".format(build)), pipe=False)
        else:
            # Snap it
            utils.call(shlex.split("btrfs sub snap {} {}".format(root, snapshot)), stdout=not quiet, pipe=quiet)

            # Spawn build script
            try:
                # Ignore --quiet if -h is passed
                # Toss stderr if --quiet is passed
                # Pass dest to builder via -d <dest>
                utils.call(shlex.split("systemd-nspawn -D {} --bind={} {}".format(snapshot, bind, build)) + args, stderr=not quiet, pipe=quiet)
            # Since we made it to this try block, make sure we delete snapshot
            finally:
                utils.call(shlex.split("btrfs sub delete {}".format(snapshot)), stdout=not quiet, pipe=quiet)
    except utils.CallException as e:
        if quiet:
            utils.dumperror(e)
        else:
            print("CallException:", e.cmd)
    except Exception as e:
        print("Caught exception:", e)
        exit(1)
    else:
        exit(0)
