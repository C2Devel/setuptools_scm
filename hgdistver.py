"""
    hgdistver
    ~~~~~~~~~

    This module is a simple drop-in to support setup.py
    in mercurial based projects.

    Its supposed to generate version numbers from mercurials metadata
    and optionally store them in a cache file which may be a text or python

    However using cachefiles is strongly suggested,
    cause distutils/setuptools won't store version numbers in sdists.

    >>> from hgdistver import get_version
    >>> version = get_version(cachefile='mypkg/__version__.py')
"""

import os


def version_from_cachefile(cachefile=None):
    if not cachefile:
        return
    with open(cachefile) as fd:
        fd.readline() # remove the comment
        try:
            line = fd.readline()
            version_string = line.split(' = ')[1].strip()
            return version_string[1:-1].decode('string-escape')
        except: # any error means invalid cachefile
            pass


def version_from_hg_id(cachefile=None):
    """stolen logic from mercurials setup.py as well"""
    if os.path.isdir('.hg'):
        import commands
        l = commands.getoutput('hg id -i -t').strip().split()
        while len(l) > 1 and l[-1][0].isalpha(): # remove non-numbered tags
            l.pop()
        if len(l) > 1: # tag found
            version = l[-1]
            if l[0].endswith('+'): # propagate the dirty status to the tag
                version += '+'
        elif len(l) == 1: #no tag found
            cmd = 'hg parents --template "{latesttag}+{latesttagdistance}-"'
            version = commands.getoutput(cmd) + l[0]

        if version.endswith('+'):
            version += time.strftime('%Y%m%d')
        return version



def _archival_to_version(data):
    """stolen logic from mercurials setup.py"""
    if 'tag' in data:
        return data['tag']
    elif 'latesttag' in data:
        return '%(latesttag)s.dev%(latesttagdistance)s-%(node).12s' % data
    else:
        return data.get('node', '')[:12]

def _data_from_archival(path):
    import email
    data = email.message_from_file(open(str(path)))
    return dict(data.items())

def version_from_archival(cachefile=None):
    #XXX: asumes cwd is repo root
    if os.path.exists('.hg_archival.txt'):
        data = _data_from_archival('.hg_archival')
        return _archival_to_version(data)

def write_cachefile(path, version):
    fd = open(path, 'w')
    try:
        fd.write('# this file is autogenerated by hgdistver + setup.py\n')
        fd.write('version = %r' % version)
    finally:
        fd.close()


methods = [
    version_from_hg_id,
    version_from_archival,
    version_from_cachefile,
]

def get_version(cachefile=None):
    try:
        version = None
        for method in methods:
            version = method()
            if version:
                return version
    finally:
        if cachefile and version:
            write_cachefile(cachefile, version)
