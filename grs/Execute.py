#!/usr/bin/env python

import os
import signal
import shlex
import subprocess
import sys
from grs.Constants import CONST

class Execute():
    """ Execute a shell command """

    def __init__(self, cmd, timeout = 1, extra_env = {}, failok = False, logfile = CONST.LOGFILE):
        """ Execute a shell command.

            cmd         - Simple string of the command to be execute as a
                          fork()-ed child.
            timeout     - The time in seconds to wait() on the child before
                          sending a SIGTERM.  timeout = None means wait indefinitely.
            extra_env   - Dictionary of extra environment variables for the fork()-ed
                          child.  Note that the child inherits all the env variables
                          of the grandparent shell in which grsrun/grsup was spawned.
            logfile     - A file to log output to.  If logfile = None, then we log
                          to sys.stdout.
        """
        def signalexit():
            pid = os.getpid()
            f.write('SENDING SIGTERM to pid = %d\n' % pid)
            f.close()
            try:
                os.kill(pid, signal.SIGTERM)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        args = shlex.split(cmd)
        extra_env = dict(os.environ, **extra_env)

        if logfile:
            f = open(logfile, 'a')
            proc = subprocess.Popen(args, stdout=f, stderr=f, env=extra_env)
        else:
            f = sys.stderr
            proc = subprocess.Popen(args, env=extra_env)

        try:
            proc.wait(timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            proc.kill()
            timed_out = True

        if not timed_out:
            # rc = None if we had a timeout
            rc = proc.returncode
            if rc:
                f.write('EXIT CODE: %d\n' % rc)
                if not failok:
                    signalexit()

        if timed_out:
            f.write('TIMEOUT ERROR: %s\n' % cmd)
            if not failok:
                signalexit()

        # Only close a logfile, don't close sys.stderr!
        if logfile:
            f.close()
