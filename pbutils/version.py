import os
from importlib import import_module
import re
import subprocess as sp

from pbutils.strings import qw


def version_bump(pkg_name, mmp, pkg_path=None):
    '''
    
    '''
    if mmp not in qw('major minor patch'):
        raise ValueError(F"'{mmp}' not in ['major', 'minor', 'patch']")

    mod = import_module(pkg_name)
    version = mod.__version__
    version_info = [int(v) for v in version.split('.')]

    if mmp == 'major':
        version_info[0] += 1
        version_info[1] = 0
        version_info[2] = 0
    elif mmp == 'minor':
        version_info[1] += 1
        version_info[2] = 0
    else:
        version_info[2] += 1
    new_version = '.'.join(map(str, version_info))

    regex = re.compile(r'^__version__ =')
    if pkg_path is None:
        init_path = os.path.join(pkg_name, '__init__.py')
    else:
        init_path = os.path.join(pkg_path, '__init__.py')

    with open(init_path) as f_in:
        with open(F"{init_path}.tmp", "w") as f_out:
            for line in f_in:
                if regex.match(line):
                    line = F"__version__ = '{new_version}'"
                print(line, file=f_out)
    ok = sp.run(['mv', F"{init_path}.tmp", init_path])
    ok.check_returncode()
    return version_info


