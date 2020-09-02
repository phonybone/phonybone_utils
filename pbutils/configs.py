import sys
import re


if sys.version_info[0] == 2:
    from future.utils import viewitems
    import ConfigParser as CP
elif sys.version_info[0] == 3:
    import configparser as CP


# Todo:
# 1. get_config should be split into two functions, one for filenames and one for data
# (and one for files?)
# 2. Further testing


class attrInterface:
    '''
    Dynamic mixin to add to ConfigParser objects to allow lookups using
    attribute syntax.
    '''
    # What this does:
    # Allow attribute-style lookup from a config object, eg
    # some_value = config.section.key2
    # It uses lazy loading to populate a generic object ('Blank') with attributes
    # looked up from the section of the config.
    def __getattr__(self, attr):
        #  this is also called by hasattr, so be careful...
        # see https://stackoverflow.com/questions/30290389/how-to-prevent-hasattr-from-retrieving-the-attribute-value-itself
        # for a possible solution

        # Is attr in the default section?
        if self.has_option(self.def_section, attr):
            return self.get(self.def_section, attr)

        if not self.has_section(attr):
            raise AttributeError(attr)

        # populate a generic object with the section's key/values:
        section_obj = type('Blank', (object,), {})()
        for key, value in self.items(attr):
            setattr(section_obj, key, value)
        setattr(self, attr, section_obj)
        return section_obj


def get_config(config_fn, defaults={}, config_type='Raw', def_section='default'):
    '''
    Return a Config object.
    '''
    with open(config_fn) as f:
        return get_config_from_data(f.read(), defaults, config_type, def_section)


def get_config_from_data(config_data, defaults={}, config_type='Raw', def_section='default'):
    '''
    Create and initialize a Config object from the given file or filename.
    Throws exceptions on missing file, syntax errors.

    Returns a ConfigParser object (subtype determined by config_type param).
    '''
    if config_type == 'Safe' and sys.version_info[0] == 3:
        clsname = 'ConfigParser'
    else:
        clsname = config_type + 'ConfigParser'
    cls = getattr(CP, clsname)
    config = cls(defaults=defaults)
    config.__class__ = type('ConfigParserPB', (cls, attrInterface), {'__init__': attrInterface.__init__})
    config.def_section = def_section

    config.read_string(config_data)
    return config


def merge_configs(dst_conf, src_conf, *sections):
    ''' merge all of src_conf[*sections] into dst_conf '''
    if len(sections) == 0:
        sections = src_conf.sections()
    for section in sections:
        dst_conf.add_section(section)
        for opt, value in src_conf.items(section):
            dst_conf.set(section, opt, value)


def inject_opts(config, opts, create_sections=True):
    '''
    Inject the contents of opts into config.
    '''
    # I don't see how this can work: attributes cannot have '.' in their
    # name.  This will put everything into the default section (which is ok?)
    try:
        section = config.def_section
    except AttributeError:
        section = 'default'

    if not config.has_section(section) and create_sections:
        config.add_section(section)

    for key, value in vars(opts).items():
        try:
            config.set(section, key, value)
        except TypeError as e:  # happens for non-RawConfigParser
            config.set(section, key, str(value))


def to_dict(config, section):
    ''' convert a config section into a dict. '''
    # This is stupid; just use config.items(section)
    return {k: v for k, v in config.items(section)}


def get_list(config, section, opt, delimiter=re.compile('[,/s]+')):
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

    for key, values in profile_values.items():
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

            if values.strip().lower() == 'true':
                setattr(obj, attrname, True)
                continue
            elif values.strip().lower() == 'false':
                setattr(obj, attrname, False)
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

def print_config(config):
    for key, section in config.items():
        print(F"[{key}]")
        for name in dict(config.items(key)):
            value = config.get(key, name)
            print(F"{name}: {value}")
    
