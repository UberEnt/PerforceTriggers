# This is the script that is responsible for finding the action handler for
# the current triggger's handler.

import os
import sys

if len(sys.argv) < 2:
    print >>sys.stderr, "Usage: %s <action>" % (sys.argv[0], )
    sys.exit(0)

action = sys.argv[1]

current_dir = os.path.dirname(__file__)
action_handler = os.path.join(current_dir, action + '.py')
if os.path.exists(action_handler):
    mod_globals = globals()
    mod_globals['__file__'] = action_handler
    execfile(action_handler, mod_globals)
