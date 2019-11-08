import sys
import os
import argparse
from types import MethodType
from importlib import import_module
from argparse import RawTextHelpFormatter  # Note: this applies to all options, might not always be what we want...

from pbutils.configs import get_config, get_config_from_data, to_dict, inject_opts, CP
from .strings import qw, ppjson
from .streams import warn


def parser_stub(docstr):
    parser = argparse.ArgumentParser(description=docstr, formatter_class=RawTextHelpFormatter)
    parser.add_argument('--config', default=_get_default_config_fn())
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    parser.add_argument('-d', action='store_true', help='debugging flag')

    # leave comments here as templates
    # parser.add_argument('required_arg')
    # parser.add_argument('--', default='', help='')
    # parser.add_argument('args', nargs=argparse.REMAINDER)

    return parser


def _get_default_config_fn():
    fn = sys.argv[0].replace('.py', '.ini')
    if not fn.endswith('.ini'):
        fn += '.ini'
    return fn


def _assemble_config(opts, default_section_name='default'):
    '''
    This builds a config by the following steps:
    1. read config file (as specified in opts, otherwise empty)
    2. inject environment vars as specified by config
    3. inject opts

    returns a ConfigParserRaw object.
    '''
    if opts.config:
        try:
            config = get_config(opts.config, config_type='Raw')
        except OSError as e:
            if e.errno is 2 and e.filename != _get_default_config_fn():
                raise
            else:
                config = get_config_from_data(f'[{default_section_name}]')
                if opts.d:
                    warn(f'skipping non-existent config file {opts.config}')

    inject_opts(config, opts)

    # add a convenience method to get opts, which are stored in the default section:
    def opt(self, opt, default=None):
        try:
            return self.get(default_section_name, opt)
        except CP.NoOptionError:
            if default is not None:
                return default
            else:
                raise
    config.opt = MethodType(opt, config)

    return config


def wrap_main(main, parser, args=sys.argv[1:]):
    '''
    create config from config file and cmd-line args;
    set os.environ['DEBUG'] if -d;
    Call main(config);
    trap exceptions; if they occur, print an error message (with optional stack trace)
      and set exit value appropriately.
    '''
    opts = parser.parse_args(args)
    config = _assemble_config(opts)

    if opts.d:
        os.environ['DEBUG'] = 'True'
        warn(opts)

    try:
        rc = main(config) or 0
        sys.exit(rc)
    except Exception as e:
        if 'DEBUG' in os.environ:
            import traceback
            traceback.print_exc()
        else:
            print('error: {} {}'.format(type(e), e))
        sys.exit(1)


def parser_config(parser, config):
    '''
    Use sections/values from the config file to initialize an argparser.
    One cmd-line arg per config section.
    '''
    for section in config.sections():
        section_dict = to_dict(config, section)
        names = ['--'+section]
        if 'short_name' in section_dict:
            names.append('-'+section_dict.pop('short_name'))

        if 'type' in section_dict:
            actual_type = eval(section_dict['type'])
            section_dict['type'] = actual_type
            if 'default' in section_dict:
                section_dict['default'] = actual_type(section_dict['default'])

        if 'action' in section_dict:
            action = section_dict['action']
            if action not in qw('store store_const store_true store_false append append_const count help version'):
                # action must be fully qualified name (module and class) of a class derived from argparse.Action
                modname, clsname = action.rsplit('.', 1)
                mod = import_module(modname)
                cls = getattr(mod, clsname)
                section_dict['action'] = cls

        parser.add_argument(*names, **section_dict)


class FloatIntStrParserAction(argparse.Action):
    '''
    Convert a string value to float, int, or str as possible.

    To be used as value to 'action' kwarg of argparse.parser.add_argument, eg:
    parser.add_argument('--some-value', action=FloatIntStrParserAction, ...)

    This is called one time for each value on command line.

    NOTE: use of this class as an Action precludes the use of the 'type' kwarg in add_argument!
    '''
    def __init__(self, **kwargs):
        super(FloatIntStrParserAction, self).__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_string):
        if self.type is not None:  # coerce to that type
            setattr(namespace, self.dest, self.type(values))
            return

        for t in [int, float, str]:  # order important
            try:
                setattr(namespace, self.dest, t(values))
                break
            except ValueError as e:
                pass
        else:
            parser.error("Error processing negc_var '{}'".format(values))  # should never get here


if __name__ == '__main__':
    def getopts(opts_ini=None):
        import argparse
        parser = argparse.ArgumentParser()

        if opts_ini:
            opts_config = get_config(opts_ini)
            parser_config(parser, opts_config)
        parser.add_argument('-v', action='store_true', help='verbose')
        parser.add_argument('-d', action='store_true', help='debugging flag')

        opts = parser.parse_args()
        if opts.d:
            os.environ['DEBUG'] = 'True'
            print(ppjson(vars(opts)))
        return opts

    # -----------------------------------------------------------------------

    opts_ini = os.path.abspath(os.path.join(os.path.dirname(__file__), 'opts.ini'))
    if not os.path.exists(opts_ini):
        warn('{}: no such file')
        opts_ini = None
    opts = getopts(opts_ini)
