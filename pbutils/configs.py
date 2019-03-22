import sys
import os
import re
from future.utils import iteritems

if sys.version_info[0] == 2:
    import ConfigParser as CP
elif sys.version_info[0] == 3:
    import configparser as CP


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


def merge_configs(dst_conf, src_conf, *sections):
    ''' merge all of src_conf[*sections] into dst_conf '''
    if len(sections) == 0:
        sections = src_conf.sections()
    for section in sections:
        dst_conf.add_section(section)
        for opt, value in src_conf.items(section):
            dst_conf.set(section, opt, value)


def inject_opts(config, opts, section='opts', coerce_strs=False):
    '''
    Add the contents of a NameSpace (opts) to a config section
    Only works with RawConfigParsers; other types interpolate values, sometimes are not interpolatable (eg bool).
    '''
    try:
        config.add_section(section)
    except CP.DuplicateSectionError:
        pass

    for opt, value in iteritems(vars(opts)):
        if coerce_strs:
            try:
                config.set(section, opt, value)
            except TypeError:
                config.set(section, opt, str(value))
        else:
            config.set(section, opt, value)


def to_dict(config, section):
    ''' convert a config section into a dict. '''
    return {k: v for k, v in config.items(section)}


def get_list(config, section, opt, delimiter=re.compile('[,\s]+')):
    ''' split a config value according to delimiter and return the list '''
    return re.split(delimiter, config.get(section, opt))


def get_slice(config, section, *keys):
    return [config.get(section, key) for key in keys]


# -----------------------------------------------------------------------
def load_attributes_from_config(obj, config, section, prepend_section=False, overwrite=False):
    '''
    Use a config/section to assign attributes to an object (or class).

    Allows lists and ranges to stored (as well as simple scalar values):
    If option name ends in '_svalues', value is assumed to be a list of string values to assign;
    If option name ends in '_ivalues', value is assumed to be a list of int values to assing;
    If option name ends in '_irange', value is assumed to be a range of ints defined by first, last, step, default;
    If option name ends in '_frange', value is assumed to be a range of floats defined by first, last, step, default;

    overwrite: if False, will only overwrite values in obj if "not hasattr(obj, attrname) or getattr(obj, attrname) is None"
    '''
    profile_values = to_dict(config, section)

    for key, values in iteritems(profile_values):
        attrname = _get_attrname(key, section, prepend_section)
        if key.endswith('_svalues'):
            _store_values(obj, key, attrname, values, str)
        elif key.endswith('_ivalues'):
            _store_values(obj, key, attrname, values, int)
        elif key.endswith('_irange'):
            _store_range_int(obj, key, attrname, values)
        elif key.endswith('_frange'):
            _store_range_float(obj, key, attrname, values)
        else:
            if not overwrite and hasattr(obj, attrname) and getattr(obj, attrname) is not None:
                continue

            for _type in (int, float):
                try:
                    setattr(obj, attrname, _type(values))
                    break
                except (TypeError, ValueError):
                    pass
            else:
                setattr(obj, attrname, values)


def _get_attrname(key, section, prepend_section):
    attrname = re.sub(r'_[is]values', '', key)  # works for ints or strings (could work for floats, too)
    attrname = key.replace('_irange', '')
    attrname = key.replace('_frange', '')
    if prepend_section:
        attrname = section + '_' + attrname
    return attrname


def _store_values(obj, key, attrname, values_str, typ):
    ''' store a list of values as an attribute  '''
    attrname = re.sub(r'_[is]values', '', key)  # works for ints or strings (could work for floats, too) (also had been commented out)
    values = map(typ, re.split(r'[\s,]+', values_str))
    default = values.pop()
    setattr(obj, attrname, values)
    if default != 'NONE':
        setattr(obj, '{}_default'.format(attrname), default)


def _store_range_int(obj, key, attrname, range_str):
    ''' store range (list) of ints as an attribute '''
    attrname = key.replace('_irange', '')  # why had this been commented out??? (see ec.tests.chomper_profile.test_load_profile_gui_values)
    first, last, inc, default = map(int, re.split(r'[\s,]+', range_str))
    values = range(first, last + 1, inc)
    setattr(obj, attrname, values)
    setattr(obj, '{}_default'.format(attrname), default)


def _store_range_float(obj, key, attrname, range_str):
    ''' store range of floats as an attribute '''
    attrname = key.replace('_frange', '')  # this was also commented out???
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


# -----------------------------------------------------------------------


def to_bool(value):
    ''' return a truthi interpretation of value, including "false" and "FalSe" as False '''
    if type(value) is bool:
        return value
    if re.match(r'false', value, re.I):
        return False
    return bool(value)
