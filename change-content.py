import fnmatch
import os
import site
import sys
import timeit

## You can include these words in your checkin description, and
## you'll enable that mode.
DEBUG_CHECKS_KEYWORD = '$DEBUG_CHECKS$'
SKIP_CHECKS_KEYWORD = '$SKIP_CHECKS$'
TIME_CHECKS_KEYWORD = '$TIME_CHECKS$'

class Timer(object):
    show_stats = True
    recursion_depth = 0

    def _duration_str(stop):
        mins, secs = divmod(int(stop - self._start), 60)
        return '{}:{:02}'.format(mins, secs)

    def __init__(self, label):
        self._label = label

    def __enter__(self):
        self._start = timeit.default_timer()
        type(self).recursion_depth  += 1
        return self

    def __exit__(self, t, v, traceback):
        stop = timeit.default_timer()
        type(self).recursion_depth  -= 1
        if type(self).show_stats:
            print '{}{} finished in {}'.format('  ' * type(self).recursion_depth, self._label, self._duration_str(stop))

P4DISPATCH_DIR = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))
if P4DISPATCH_DIR not in sys.path:
    sys.path.insert(0, P4DISPATCH_DIR)
site.addsitedir(os.path.join(P4DISPATCH_DIR, '..', 'thirdparty', 'python-packages'))

import yaml

import p4

def exists_after_change(files, cl, file):
    if file in files:
        cl = '=' + cl
    return p4.fstat('%s@%s' % (file, cl))['exists']

def unity_meta_check(changelist, change, matched_files):
    with Timer("Verifying added assets"):
        metas_correctly_added = verify_metas_added(changelist, change, matched_files)
    with Timer("Verifying deleted assets"):
        metas_correctly_deleted = verify_no_orphaned_files(changelist, change, matched_files)
    with Timer("Modified meta file guids"):
        no_meta_guids_modified = verify_no_guid_modifications(changelist, change, matched_files)

    # TODO(jorgenpt): Add a check for duplicate use of GUIDs. This needs a GUID cache (since
    # enumerating all of them can be slow,) as well as a reliable way to determine project root.

    return metas_correctly_added and metas_correctly_deleted and no_meta_guids_modified

CREATE_FILE_ACTIONS = set(['branch', 'add', 'import'])

def verify_metas_added(cl, change, matched_files):
    assets = set(fnmatch.filter(matched_files, '*/Assets/*'))
    missing_metas = False
    for asset in assets:
        if asset.endswith('.meta'):
            continue

        if os.path.basename(asset).startswith('.'):
            continue

        action = change['files'][asset]['action']
        if action not in CREATE_FILE_ACTIONS:
            continue

        # TODO(jorgenpt): Might be able to optimize this by batching the fstat calls.

        file_meta_exists = exists_after_change(matched_files, cl, '%s.meta' % asset)
        if not file_meta_exists:
            missing_metas = True
            print >>sys.stderr, "\nYou need to check in the matching meta file for %s" % asset,

    return not missing_metas

DELETE_FILE_ACTIONS = set(['move/delete', 'delete', 'purge', 'archive'])

def verify_no_orphaned_files(cl, change, matched_files):
    assets = set(fnmatch.filter(matched_files, '*/Assets/*'))
    orphaned_files = False
    for asset in assets:
        action = change['files'][asset]['action']
        if action not in DELETE_FILE_ACTIONS:
            continue

        other_half_of_meta_pair = '%s.meta' % asset
        if asset.endswith('.meta'):
            other_half_of_meta_pair, ext = os.path.splitext(asset)

        other_half_of_meta_pair_exists = exists_after_change(matched_files, cl, other_half_of_meta_pair)
        if other_half_of_meta_pair_exists:
            orphaned_files = True
            print >>sys.stderr, "\nYou need to delete %s if you're deleting %s" % (other_half_of_meta_pair, asset),

    return not orphaned_files

def verify_no_guid_modifications(cl, change, matched_files):
    metas = fnmatch.filter(matched_files, '*/Assets/*.meta')
    mutated_metas = False
    for asset in metas:
        assetChange = change['files'][asset]
        action = assetChange['action']
        if action != 'edit':
            continue

        new_meta = yaml.load(p4.printfile('%s@=%s' % (asset, cl)))
        old_meta = yaml.load(p4.printfile('%s#%s' % (asset, assetChange['rev'])))

        if 'guid' in new_meta and 'guid' in old_meta:
            if new_meta['guid'] != old_meta['guid']:
                mutated_metas = True
                print >>sys.stderr, "\nYou're not allowed to change the guid of an existing asset %s" % asset,
    return not mutated_metas

# These are the valid types for content_checker_config.yaml
CHECK_TYPES = {
    'unity_meta_check': unity_meta_check
}

def main(changelist):
    change = p4.describe(changelist)
    if DEBUG_CHECKS_KEYWORD in change['desc']:
        p4.DEBUG = True
        change = p4.describe(changelist)

    if SKIP_CHECKS_KEYWORD in change['desc']:
        return True

    Timer.show_stats = TIME_CHECKS_KEYWORD in change['desc']
    checks_succeeded = True

    config_path = os.path.join(P4DISPATCH_DIR, 'content_checker_config.yaml')
    if not os.path.exists(config_path):
        print >>sys.stderr, "Unable to find a P4 content checker configuration file at '%s'" % config_path
        return True

    try:
        checks = yaml.load(open(config_path, 'r'))

        for (name, info) in checks.iteritems():
            check_name = info['check']
            check = CHECK_TYPES.get(check_name)
            if not check:
                print >>sys.stderr, "Unable to find a check with name %r" % check_name
                continue

            matched_files = []
            for path_pattern in info['paths']:
                matched_files += fnmatch.filter(change['files'].iterkeys(), path_pattern)

            if matched_files:
                with Timer('Checker "%s"' % name):
                    if not check(changelist, change, matched_files):
                        checks_succeeded = False

        if not checks_succeeded:
            print >>sys.stderr, "\n\nFix the problems above, or if you're intentionally doing this, ask a developer for help."
    except Exception as e:
        print >>sys.stderr, "Encountered an error trying to validate your change: %r" % e


    return checks_succeeded

if __name__ == '__main__':
    if main(sys.argv[2]):
        sys.exit(0)
    else:
        sys.exit(1)
