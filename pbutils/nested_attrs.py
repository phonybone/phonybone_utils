'''
set_nested_attr(obj, nattr, value)
'''
import re

class __Blank:
    ''' Empty class with a __str__() method '''
    def __str__(self):
        return str(self.__dict__)


def set_nested_attr(obj, nattr: str, value):
    '''
    Recursively set attributes on an object.

    @Params
    - obj: target object
    - nattr: attribute name, may be '.'-separated.  If so, finds and sets
      an attribute by creating sub-objects according to nattr as needed.
    - value: value to assign to target attribute.

    Example:
    set_nested_attr(some_obj, 'lvl1.lvl2.lvl3', 'some_value') has the effect
    of:
    setattr(some_obj, 'lvl1', object())
    setattr(some_obj.lvl1, 'lvl2', object())
    setattr(some_obj.lvl1.lvl2, 'lvl3', 'some_value')

    with each level of sub-object created as needed (note: will overwrite existing
    sub-objects!)

    and then:
    getattr(some_obj.lvl1.lvl2, 'lvl3') == 'some_value)
    '''
    path = [p for p in nattr.split('.') if len(p)]
    if not path:
        print(F"skipping nattr={nattr}")
        return

    for part in path[:-1]:
        sect = getattr(obj, part, None)
        if sect is None:
            sect = __Blank()
            setattr(obj, part, sect)
        obj = sect
    setattr(obj, path[-1], value)


def get_nested_attr(obj, nattr):
    ''' get a single nested attribute '''
    path = nattr.split('.')
    for part in path[:-1]:
        obj = getattr(obj, part)
    return getattr(obj, path[-1])


def get_nested_attrs(obj, path=None):
    ''' generate all nested attrbutes ("leafs" only) '''
    if not hasattr(obj, '__dict__'):
        return

    if path is None:
        path = []

    for key, val in obj.__dict__.items():
        if not hasattr(val, '__dict__'):  # is a "scalar"
            jpath = '.'.join(path) + '.' + key if path else key
            yield jpath, val
        else:
            yield from get_nested_attrs(val, path+[key])

def config_from_lines(lines):
    '''
    Given an iterable set of lines, return a config object 
    (type(config) is __Blank) that can be accessed using
    get_nested_attr(s).
    
    Sections are introduced by a line of form: "[Section_name]"
    If a section is defined, all following values have the section
    name pre-pended to them (until a new section is introduced).

    Lines of the form "key: value" are added to the current section.
    "key" is a '.'-delimited string (with 0 or more '.'s); 
    "value" is a string.  If the value can successfully converted
      to a float, int, or bool ("
    
    '''
    config = __Blank()
    sect_regex = re.compile(r'^\[(\w+)]$')
    val_regex = re.compile(r'^(\w[_\w.]*): (.*)$')
    current_section = config

    for line in lines:
        mg = sect_regex.match(line)
        if mg:
            section_name = mg.group(1)
            current_section = __Blank()
            setattr(config, section_name, current_section)
            print(F"new section [{section_name}]")
            continue

        mg = val_regex.match(line)
        if not mg:
            continue

        nattr, value = mg.group(1), mg.group(2)
        value = __convert_value(value)
        set_nested_attr(current_section, nattr, value)
    return config


def config_from_file(filename):
    with open(filename) as myfile:
        return config_from_lines(myfile.read().split('\n'))


_bool_regex = re.compile(r'^true|false$', flags=re.I)
def __convert_value(value):
    if _bool_regex.match(value):
        return value.lower() == 'true'
    try:
        return int(value)
    except Exception:
        try:
            return float(value)
        except Exception:
            return value


if __name__ == '__main__':
    data = '''
blank.key1: value1

blank.section1.key1: s1k1
blank.section1.key2: s1k2
blank.section2.key2: s2k2
blank.section1.key3: s1k3

Fart.key1: value1
Fart.section1.key1: s1k1
Fart.section1.key2: s1k2
Fart.section2.key2: s2k2
Fart.section1.key3: s1k3

Fart.sec1.sec2.key1: s1s2k1
Fart.sec1.sec1.key2: s1s1k2
Fart.sec1.sec2.key2: s1s2k2
Fart.sec1.sec2.key3: s1s2k3

[section1]
flintstone.fred: father
flintstone.wilma: mother
flintstone.pebbles: daughter
flintstone.dino: dog
flintstone.friends.fred: barney
flintstone.friends.wilma: betty
flintstone.friends.pebbles: bambam
flintstone.n_members: 4

[bikes]
honda.1988.nt650.engine.displacement: 647cc
honda.1988.nt650.engine.type: 4-stroke
honda.1988.nt650.engine.cooling: H20
honda.1988.nt650.swing_arm.single_sided: True
honda.1988.nt650.brakes.front.dual_disk: faLsE
'''

    # parse data to build objects with the defined nested attributes.
    # inject top-level objects into globals() dict.
    config = config_from_lines(data.split('\n'))

    print('-' * 72)
    for path, value in get_nested_attrs(config):
        print(F"{path} = {value} ({type(value)})")
