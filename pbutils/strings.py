'''
Random string utils.
'''

import re
import json

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
            start,stop = map(int, r.split('-'))
            ranges.extend(xrange(start, stop+1))
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
    def default(self, obj):
        if hasattr(obj, 'as_json'):
            return obj.as_json()
        if type(obj) is set:
            return map(str, obj)
        try:
            return json.JSONEncoder.default(self, obj)
        except:
            return str(obj)

def ppjson(data, indent=2):
    return json.dumps(data, indent=indent, cls=StringEncoder)
    
def qw(s, rx=None):
    if s == '':
        return []
    if rx is not None:
        rx = re.compile(rx)     # apparently one can safely re-compile regexes, so this handles strings and rx's...
        return re.split(rx, s)
    else:
        return s.split(' ')

if __name__ == '__main__':
    def test_ppjson():
        import datetime as dt

        class Foo(object):
            fmt = '%a, %m %d %Y'
            def __init__(self, string, dob, z):
                self.string = string
                self.dob = dob
                self.z = z

            def as_json(self):
                return {
                    'string': self.string,
                    'dob': self.dob.strftime(self.fmt),
                    'z': repr(self.z)
                    }


        foo = Foo('fred', dt.datetime.now(), 3+2j)
        print('foo: {}'.format(ppjson(foo)))
    #test_ppjson()

    def test_qw():
        fodder = 'list, of, strings,   not,always, separated consistently'
        print(qw(fodder))
        print(qw(fodder, '[\s,]+'))
        print(qw(fodder, re.compile('[\s,]+')))
        print(qw(fodder, re.compile('s')))
        print(qw(fodder, 's'))
    test_qw()
                 
