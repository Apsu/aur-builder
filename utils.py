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

def call(cmd, newlines=True, sets=False, exceptions=True, combine=False, stdout=True, stderr=True, pipe=False, **kwargs):
    """
    Simple Popen wrapper returning stdout, stderr, returncode, command
    newlines=Toggles universal_newlines
    sets=True will wrap stdout/stderr in set()
    exceptions=True will raise an exception on !0 process exit
    pipe=True will log stdout/stderr as received (and return None, None)
    combine=True will combine stderr with stdout
    stdout=False will pipe stdout to /dev/null
    stderr=False will pipe stderr to /dev/null
    """
    with subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL if not stdout else subprocess.PIPE if pipe else sys.stdout, stderr=subprocess.DEVNULL if not stderr else subprocess.STDOUT if combine else subprocess.PIPE if pipe else sys.stderr, universal_newlines=newlines, **kwargs) as process:
        if pipe:
            try:
                stdout, stderr = process.communicate()
            except KeyboardInterrupt:
                print("Interrupt!")
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
