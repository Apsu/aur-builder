import sys
import subprocess

def bail(msg):
    """Easier exception raising"""
    raise Exception(msg)

class CallException(Exception):
    def __init__(self, args):
        self.cmd, self.stdout, self.stderr, self.code = self.args = args
    def __str__(self):
        return repr(self.args)

def dumperror(e):
    print("Error calling '{}':".format(e.cmd))
    print("Stdout:", e.stdout)
    print("Stderr:", e.stderr, file=sys.stderr)
    print("Return:", e.code)

def call(cmd, sets=False, exceptions=False, log=False, combine=False, **kwargs):
    """
    Simple Popen wrapper returning stdout, stderr, returncode
    sets=True will wrap stdout/stderr in set()
    exceptions=True will raise an exception on !0 process exit
    log=True will log stdout/stderr to console as received
    combine=True will combine stderr with stdout
    """
    with subprocess.Popen(cmd, stdout=sys.stdout if log else subprocess.PIPE, stderr=subprocess.STDOUT if combine else sys.stderr if log else subprocess.PIPE, universal_newlines=True, **kwargs) as process:
        if log:
            stdout, stderr = None, None
        else:
            stdout, stderr = process.communicate()

        code = process.returncode
        if exceptions and code:
            raise CallException((cmd, stdout, stderr, code))
        else:
            if sets:
                return set(stdout.split()) if stdout else set(), set(stderr.split()) if stderr else set(), code, cmd
            else:
                return stdout, stderr, code, cmd
