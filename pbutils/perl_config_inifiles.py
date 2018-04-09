#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
# Attempt to read a Chomper-style Config::IniFiles file using StringIO and ConfigParser.
# see https://stackoverflow.com/questions/2819696/parsing-properties-file-in-python/2819788#2819788
# or not

Author: Victor Cassen
'''

import sys
import os
import re
import tempfile
from StringIO import StringIO
from ConfigParser import ConfigParser


def coroutine_closure(*a, **kw):
    '''
    Coroutine that takes initial args
    '''
    # see https://stackoverflow.com/questions/5929107/decorators-with-parameters
    def decor(f):               # *a, **kw):
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        wrapper = wrapper(*a, **kw)
        next(wrapper)
        return wrapper
    return decor


def read_perl_config_ini(self, ini_file, dummy_section='_dummy_'):):
    ''' 
    Return a ConfigParser() object from a perl config::inifiles type file.
    Basic differences:
    - config::inifiles allow "key=<<value"-style multi-line assignments;
    - config::inifiles do not require an initial [section]; if missing
      from ini_file, insert a "dummy" section.
    '''

    in_multiline = False
    key, endkey = False, False
    multiline_value = ''
    multiline_assignment_rx = re.compile('^(\w+)=<<(\w+)')
    section_header_rx = re.compile(r'\[(\w+)\]')

    fio = StringIO()
    @coroutine_closure(fio)
    def acc(fio):
        while True:
            line = (yield)
            if line is None:
                break
            fio.write(line)
            fio.write('\n')

    def emit(line):
        acc.send(line)

    # read config file, build contents in fio:
    with open(ini_file) as f:
        first_line = next(f).strip()
        if not section_header_rx.match(first_line):
            emit('[{}]'.format(dummy_section))
        emit(first_line)

        for line in (l.strip() for l in f):
            line = __strip_comments(line)
            if not in_multiline:
                mg = multiline_assignment_rx.match(line)
                if mg:
                    key = mg.group(1)
                    endkey = mg.group(2)
                    in_multiline = True
                    multiline_value = ''
                else:
                    emit(line)
            else:
                if line == endkey:
                    emit('{}={}'.format(key, multiline_value))
                    key, endkey = False, False
                    in_multiline = False
                else:
                    multiline_value += line

    tmp = tempfile.TemporaryFile()
    tmp.write(fio.getvalue())
    tmp.seek(0, 0)

    # create ConfigParser from fio:
    conf =  ConfigParser()
    conf.readfp(tmp)
    return conf

def __strip_comments(self, line):
    idx = line.find('#')
    if idx >= 0:
        return line[:idx]
    else:
        return line

def write_perl_config_ini(self, conf, conf_fn, dummy_section=None):
    def _write_section(fp, conf, section, is_dummy_section=False):
        if not is_dummy_section:
            fp.write('[{}]\n'.format(section))
        for key, value in conf.items(section):
            if value is None:
                value=''
            fp.write('{}={}\n'.format(key, value))
        fp.write('\n')

    with open(conf_fn, 'w') as fp:
        if dummy_section is not None:
            _write_section(fp, conf, dummy_section, is_dummy_section=True)

        for section in conf.sections():
            if section == dummy_section:
                continue
            _write_section(fp, conf, section)

if __name__=='__main__':
    def main(opts):
        config = read_perl_config_ini(opts.ini_file)
        print("{} Sections".format(len(config.sections())))

        out_fn = opts.ini_file + '.bak'
        write_perl_config_ini(config, out_fn, dummy_section='_dummy_')
        print('{} written'.format(out_fn))

    def getopts():
        import argparse
        from argparse import RawTextHelpFormatter # Note: this applies to all options, might not always be what we want...
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)
        parser.add_argument('ini_file')
        parser.add_argument('--some_arg', default='some arg')
        parser.add_argument('-v', action='store_true', help='verbose')
        parser.add_argument('-d', action='store_true', help='debugging flag')
        # parser.add_argument('args', nargs=argparse.REMAINDER)

        opts=parser.parse_args()
        if opts.d:
            os.environ['DEBUG'] = 'True'
            print opts
        return opts
        


    opts = getopts()
    try:
        rc = main(opts)
        if rc is None:
            rc = 0
        sys.exit(rc)
    except Exception as e:
        if opts.d:
            import traceback
            traceback.print_exc()
        else:
            print 'error: {} {}'.format(type(e), e)
        sys.exit(1)
