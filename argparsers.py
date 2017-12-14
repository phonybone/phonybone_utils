import argparse

from configs import get_config, to_dict
from strings import qw, ppjson
from importlib import import_module




def parser_config(parser, config):
    ''' 
    Use sections/values from the config file to initialize an argparser.
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
        if self.type is not None: # coerce to that type
            setattr(namespace, self.dest, self.type(values))
            return
        
        for t in [int, float, str]: # order important
            try:
                setattr(namespace, self.dest, t(values))
                break
            except ValueError as e:
                pass
        else:
            parser.error("Error processing negc_var '{}'".format(values)) # should never get here
        


if __name__=='__main__':
    import sys, os
    

    def getopts(opts_ini=None):
        import argparse
        parser = argparse.ArgumentParser()

        if opts_ini:
            opts_config = get_config(opts_ini)
            parser_config(parser, opts_config)
        parser.add_argument('-v', action='store_true', help='verbose')
        parser.add_argument('-d', action='store_true', help='debugging flag')

        opts=parser.parse_args()
        if opts.d:
            os.environ['DEBUG'] = 'True'
            print ppjson(vars(opts))
        return opts


    #-----------------------------------------------------------------------

    opts_ini = os.path.abspath(os.path.join(os.path.dirname(__file__), 'opts.ini'))
    if not os.path.exists(opts_ini):
        warn('{}: no such file')
        opts_ini = None
    opts = getopts(opts_ini)
            
