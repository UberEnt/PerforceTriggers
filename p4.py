import marshal
import os
import subprocess
import tempfile

DEBUG = False

class PerforceException(Exception):
    pass

def _invoke(*args):
    results = []
    fd, tempfname = tempfile.mkstemp()
    try:
        os.close(fd)
        with open(tempfname, 'w+b') as tempf:
            cmd = ['p4.exe', '-G'] + list(args)
            if DEBUG:
                print '$ %r' % cmd
            process = subprocess.Popen(cmd, stdout=tempf)
            process.communicate()
            tempf.seek(0)

            try:
                while 1:
                    record = marshal.load(tempf)
                    results.append(record)
            except EOFError:
                pass

            if process.returncode != 0:
                raise PerforceException('command %r return error: %d' % (cmd, process.returncode))
    finally:
        os.unlink(tempfname)

    return results

DESCRIBE_PATH_KEYS = ['depotFile', 'rev', 'action', 'type', 'fileSize', 'digest']

def describe(cl):
    obj = _invoke('describe', cl)[0]

    fileKeys = filter(lambda k: k.startswith('depotFile'), obj.iterkeys())
    files = {}

    for key in fileKeys:
        key_suffix = key[len('depotFile'):]
        file_obj = {}
        for subkey in DESCRIBE_PATH_KEYS:
            specific_subkey = subkey + key_suffix
            if specific_subkey in obj:
                file_obj[subkey] = obj[specific_subkey]
                del obj[specific_subkey]
        files[file_obj['depotFile']] = file_obj

    obj['files'] = files

    if DEBUG:
        print '> %r' % obj

    return obj

DELETED_ACTIONS = set(['delete', 'move/delete', 'purge'])

def fstat(file):
    obj = _invoke('fstat', file)[0]

    if obj.get('code') == 'error':
        if DEBUG:
            print '! %r' % obj
        obj = { 'exists': False }
    else:
        obj['exists'] = obj.get('headAction') not in DELETED_ACTIONS

    if DEBUG:
        print '> %r' % obj

    return obj

def files(pattern):
    results = _invoke('files', pattern)
    if len(results) == 1 and results[0].get('code') == 'error':
        if DEBUG:
            print '! %r' % obj
        results = []

    for result in results:
        result['exists'] = result.get('action') not in DELETED_ACTIONS

    if DEBUG:
        print '> %r' % results

    return results

def printfile(file):
    results = _invoke('print', file)
    meta = results[0]
    if meta.get('code') == 'error':
        if DEBUG:
            print '! %r' % meta
            print '> None'
        return None

    text = results[1]['data']
    if DEBUG:
        print '> (... %i byte(s))' % len(text)
    return text
