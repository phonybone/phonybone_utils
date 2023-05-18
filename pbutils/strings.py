'''
Random string utils.
'''

import re
import json
from functools import partial

def qw(s, rx=None):
    '''
    Perl-style quoting: qw("this that these those") returns ["this", "that" ,"these", "those"]
    Splits input string on regular exp rx, or ' ' if not provided.
    '''
    if s == '':
        return []
    if rx is not None:
        rx = re.compile(rx)     # apparently one can safely re-compile regexes, so this handles strings and rx's...
        return re.split(rx, s)
    else:
        return s.split(' ')


# add a random comment

def expand_range_list(src):
    '''
    Given a string representing a list of integer-based ranges,
    return a list with an element for each member in the range.
    Ranges may be:
    - a single integer
    - a range denoted as 'x - y'

    Lists of ranges are separated by commas.
    White space is ignored.

    Example:
    If src="1,2,5,6-9, 11, 14 - 15", then the list
    [1,2,5,6,7,8,9,11,14,15] is returned.

    Note that although the example above is sorted, no such requirements are imposed or
    considered by this function.
    '''

    # Strip all whitespace:
    src = re.sub(r'\s+', '', src)
    ranges = []
    for r in src.split(','):
        if '-' in r:
            start, stop = map(int, r.split('-'))
            ranges.extend(range(start, stop + 1))
        else:
            ranges.append(int(r))
    return ranges


def chunks(s, ll):
    '''
    Given a string s, return a list of string of max length ll.
    The final string in this list will contain the remainder of s.

    Example: chucks('abcdefghijkl', 5) returns ['abcde', 'fghij', 'kl']
    '''
    i, j = 0, ll
    chunks = []
    while True:
        chunk = s[i:j]
        if len(chunk) > 0:
            chunks.append(chunk)
        if len(chunk) < ll:
            break
        i += ll
        j += ll
    return chunks


class StringEncoder(json.JSONEncoder):
    '''
    Attempt to JSON encode anything.
    First looks for an object method named 'as_json'
    and invokes it if found.
    Otherwise, attempts to convert sets to a string.
    Otherwise, tries the default.  If that failes, returns
    str(x)
    '''
    def default(self, obj):
        if hasattr(obj, 'as_json'):
            return obj.as_json()
        if type(obj) is set:
            return map(str, obj)
        try:
            return json.JSONEncoder.default(self, obj)
        except Exception:
            return str(obj)


json2 = partial(json.dumps, indent=2, cls=StringEncoder)

# PrettyFloat approach from here: https://stackoverflow.com/questions/1447287/format-floats-with-standard-json-module
def ppjson(data, indent=2, float_prec=2):
    '''
    Return a nicely-formatted JSON blob base on data.
    data can be any pretty much anything.  Objects that don't JSON-serialize
    well are serialized as str(obj) unless data has a callable attribute named
    'as_json', in which case that is called.
    '''
    return json.dumps(pretty_floats(data, float_prec), indent=indent)


class PrettyFloat:
    ''' Print floating point numbers with given precision '''
    def __init__(self, value, prec=2):
        self.value = value
        self.prec = prec

    def __repr__(self):
        return f'%.{self.prec}f' % self.value


def pretty_floats(obj, float_prec):
    ''' Recursively string-ify an object, using PretyFloat for floating point values '''
    if isinstance(obj, float):
        return repr(PrettyFloat(obj, float_prec))
    elif isinstance(obj, dict):
        return {k: pretty_floats(v, float_prec) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [pretty_floats(o, float_prec) for o in obj]
    elif hasattr(obj, 'as_json') and callable(obj.as_json):
        return obj.as_json()
    elif hasattr(obj, '__dict__'):
        return pretty_floats(obj.__dict__, float_prec)
    return str(obj)


if __name__ == '__main__':
    def test_ppjson():
        import datetime as dt
        import uuid

        class Foo(object):
            ''' some random class that implements as_json() '''
            fmt = '%a, %m %d %Y'

            def __init__(self, str, dob, z, flt):
                self.string = str
                self.dob = dob
                self.z = z
                self.flt = flt
                self.uuid = uuid.uuid4()

            def as_json(self):
                ''' as_json() must return a JSON-serializable version of self. '''
                return {
                    'string': self.string,
                    'dob': self.dob.strftime(self.fmt),
                    'z': repr(self.z),
                    'flt': self.flt,
                    'flt3': repr(PrettyFloat(self.flt, 3)),
                    'uuid_str': str(self.uuid),
                }

        foo = Foo('fred', dt.datetime.now(), 3+2j, 23.238932)
        print(F"foo: {ppjson(foo)}")
        print(F"foo.__dict__.pretty (bypasses foo.as_json): {ppjson(foo.__dict__, float_prec=1)}")

        for p in range(10):
            print(ppjson(3.14159254, float_prec=p))
    test_ppjson()

    def test_qw():
        fodder = 'list, of, strings,   not,always, separated consistently'
        print(qw(fodder))
        print(qw(fodder, r'[\s,]+'))
        print(qw(fodder, re.compile(r'[\s,]+')))
        print(qw(fodder, re.compile(r's')))
        print(qw(fodder, 's'))
#    test_qw()



