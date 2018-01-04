import os
import ConfigParser as CP
import re

from strings import qw

def get_config(config_fn, defaults={}, config_type='Safe'):
    '''
    Create and initialize a Config object from the given file.  Throws exceptions on missing file, syntax errors.
    '''
    if not os.path.exists(config_fn):
        raise OSError("{}: no such file".format(config_fn))
    clsname = '{}ConfigParser'.format(config_type)
    cls = getattr(CP, clsname)
    config = cls(defaults=defaults)
    consumed_files = config.read(config_fn)
    if len(consumed_files) == 0:
        raise RuntimeError("unable to read config file {}".format(config_fn))
    return config


def inject_opts(config, opts, section='opts'):
    ''' 
    Add the contents of a NameSpace (opts) to a config section 
    Only works with RawConfigParsers; other types interpolate values, some times are not interpolatable (eg bool).
    '''
    try:
        config.add_section(section)
    except CP.DuplicateSectionError:
        pass

    for opt, value in vars(opts).iteritems():
        config.set(section, opt, value)

def to_dict(config, section):
    ''' convert a config section into a dict. '''
    return {k:v for k,v in config.items(section)}


def get_list(config, section, opt, delimiter=re.compile('[,\s]+')):
    ''' split a config value according to delimiter and return the list '''
    return re.split(delimiter, config.get(section, opt))

def get_slice(config, section, *keys):
    return [config.get(section, key) for key in keys]

#-----------------------------------------------------------------------
def load_attributes_from_config(obj, config, section):
    ''' 
    Use a config/section to assign attributes to an object (or class).
    
    Allows lists and ranges to stored (as well as simple scalar values):
    If option name ends in '_svalues', value is assumed to be a list of string values to assign;
    If option name ends in '_ivalues', value is assumed to be a list of int values to assing;
    If option name ends in '_irange', value is assumed to be a range of ints defined by first, last, step, default;
    If option name ends in '_frange', value is assumed to be a range of floats defined by first, last, step, default;
    '''
    profile_values = to_dict(config, section)
    for key, values in profile_values.iteritems():
        if key.endswith('_svalues'):
            _store_values(obj, key, values, str)
        elif key.endswith('_ivalues'):
            _store_values(obj, key, values, int)
        elif key.endswith('_irange'):
            _store_range_int(obj, key, values)
        elif key.endswith('_frange'):
            _store_range_float(obj, key, values)
        else:
            setattr(obj, key, value)


def _store_values(obj, key, values_str, typ):
    ''' store a list of values as an attribute  '''
    attrname = re.sub(r'_[is]values', '', key)
    values = map(typ, re.split(r'[\s,]+', values_str))
    default = values.pop()
    setattr(obj, attrname, values)
    setattr(obj, '{}_default'.format(attrname), default)

def _store_range_int(obj, key, range_str):
    ''' store range (list) of ints as an attribute '''
    attrname = key.replace('_irange', '')
    first, last, inc, default = map(int, re.split(r'[\s,]+', range_str))
    values = range(first, last+1, inc)
    setattr(obj, attrname, values)
    setattr(obj, '{}_default'.format(attrname), default)


def _store_range_float(obj, key, range_str):
    ''' store range of floats as an attribute '''
    attrname = key.replace('_frange', '')
    first, last, inc, default = map(float, re.split(r'[\s,]+', range_str))
    if first >= last:
        raise ValueError('{} >= {}'.format(first, last))
    val = first
    values = []
    while val <= last:
        values.append(val)
        val += inc
    setattr(obj, attrname, values)
    setattr(obj, '{}_default'.format(attrname), default)
#-----------------------------------------------------------------------
