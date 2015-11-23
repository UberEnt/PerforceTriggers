# This file is not directly used from Perforce, but it is the
# script on the Perforce daemon that is responsible for updating & executing
# the second-level bootstrap script, in bootstrap.py.

import os
import subprocess
import sys

SECOND_STAGE_WORKSPACE = 'perforce-admin-tools'
SECOND_STAGE_RELATIVE_PATH = ("tools", "p4dispatch", "bootstrap.py")

devnull = open(os.devnull, 'w')
subprocess.check_call(["p4.exe", "-c%s" % SECOND_STAGE_WORKSPACE, "sync"], stdout=devnull, stderr=devnull)

current_dir = os.path.dirname(__file__)
second_stage = os.path.join(current_dir, *SECOND_STAGE_RELATIVE_PATH)
if os.path.exists(second_stage):
    mod_globals = globals()
    mod_globals['__file__'] = second_stage
    execfile(second_stage, mod_globals)
