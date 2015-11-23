This is a small set of scripts that does two things:

 - Route Perforce triggers to appropriate scripts (to make it easier to add new Perforce triggers with just a `p4 triggers` update and a new script in Perforce.)
  - We currently use a version of Perforce that does not support the `%//depot/path/to/script%` syntax in p4 triggers, so that makes this more important.
 - Verifies Unity meta-file consistency for configured projects.

The Unity meta-file verification has three checks:

 - Verify that any new `Asset` has a new .meta file added for it.
 - Verify that any deleted `Asset` also has its .meta file deleted.
 - Verify that no-one attempts to modify the guid field of an existing .meta file.

This prevents a lot of common mistakes that happen with Perforce and Unity.

It does not **yet** support two more checks that would be helpful:

 - Verify that any new `Asset` does not re-use an existing guid.
 - Verify that there are no .meta files added without the corresponding `Asset`.

Here, `Asset` means any file under the `Assets` directory in a project configured in `content_checker_config.yaml`.

# Setting up

First, you need to set up a workspace for use by your Perforce server to check out the scripts. This is what ours looks like:

    Client: perforce-admin-tools

    Root:   d:\PerforceTriggers\tools\

    View:
            //depot/admin/tools/... //perforce-admin-tools/...

For us, these scripts live in e.g. `//depot/admin/tools/p4dispatch/bootstrap.py`.

Copy `root_bootstrap.py` onto your Perforce server to wherever. For us, we use `D:\PerforceTriggers`. You will have to update `root_bootstrap.py` to
have the correct path to `bootstrap.py` in `SECOND_STAGE_RELATIVE_PATH`. You will also have to update it to have the correct name of the workspace in `SECOND_STAGE_WORKSPACE`.

Install [PyYAML](pyyaml).

Configure `p4 triggers` to launch `root_bootstrap.py` as follows:

    gatekeeper-content change-content //depot/... "C:\python27\python.exe D:\PerforceTriggers\root_bootstrap.py change-content %changelist%"

You will have to update the Python path as appropriate. That should be all!

# Parts

## root_bootstrap.py

This script is just responsible for syncing the `SECOND_STAGE_WORKSPACE` and launching `bootstrap.py` from this repository.

## bootstrap.py

This script checks for a file called `$action.py` where `$action` is the Perforce trigger we're executing for, like change-content, change-commit, etc,
and if it exists it launches it. It sets up some import paths first.

## change-content.py

This script reads `content_checker_config.yaml`, and if any of the files changed in this change match the `paths` in a project,
it launches the check, rejecting a change if it fails the check. The only support check so far is a Unity meta file check.


# Questions?

If you have any questions, file an issue or contact the author at jorgenpt@gmail.com.

[pyyaml]: http://pyyaml.org/wiki/PyYAML
