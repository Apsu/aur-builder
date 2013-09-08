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

def call(cmd, newlines=True, sets=False, exceptions=True, combine=False, pipe=False, **kwargs):
    """
    Simple Popen wrapper returning stdout, stderr, returncode, command
    newlines=Toggles universal_newlines
    sets=True will wrap stdout/stderr in set()
    exceptions=True will raise an exception on !0 process exit
    pipe=True will log stdout/stderr as received (and return None, None)
    combine=True will combine stderr with stdout
    """
    with subprocess.Popen(cmd, stdout=subprocess.PIPE if pipe else sys.stdout, stderr=subprocess.STDOUT if combine else subprocess.PIPE if pipe else sys.stderr, universal_newlines=newlines, **kwargs) as process:
        if pipe:
            stdout, stderr = process.communicate()
        else:
            stdout, stderr = None, None
            process.wait()

        code = process.returncode
        if exceptions and code:
            raise CallException((cmd, stdout, stderr, code))
        else:
            if sets:
                return set(stdout.split()) if stdout else set(), set(stderr.split()) if stderr else set(), code, cmd
            else:
                return stdout, stderr, code, cmd
