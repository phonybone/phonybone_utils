'''
Random string utils.
'''

import re

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
    The final string in this list will contain the remainder of
    s.
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


import json
class StringEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) is set:
            return map(str, obj)
        try:
            return json.JSONEncoder.default(self, obj)
        except:
            return str(obj)

def ppjson(data, indent=2):
    return json.dumps(data, indent=indent, cls=StringEncoder)
    
def qw(s):
    if s == '':
        return []
    return s.split(' ')
