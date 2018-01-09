def grow(l, n, f):
    filler = [f() for _ in xrange(n)]
    l.extend(filler)

def grow_to(l, n, fill=None):
    amount = n - len(l)
    if amount > 0:
        grow(l, amount, fill)
    return l[n-1]

def maxspan(spans):
    ''' given a list of spans (tuples), return the bounding span '''
    return (min([s[0] for s in spans]), max([s[1] for s in spans])) # yes there are faster ways
    
def flatten(l):
    ''' l is a list comprised of sub-lists or tuples.  Return a 1D list containing all the elements of l in order. '''
    # see https://stackoverflow.com/questions/10632839/python-transform-list-of-tuples-in-to-1-flat-list-or-1-matrix
    return list(sum(l, ()))

if __name__ == '__main__':
    lol = [[] for _ in xrange(3)]
    assert(len(lol) == 3)
    l6 = grow_to(lol, 6, list)
    print 'lol: {}'.format(lol)
    print 'l6: {}'.format(l6)
    assert(len(lol) == 6)
    assert(all(map(lambda l: type(l) is list, lol)))
    assert(len(l6) == 0)

    lol[0].extend(['fred', 'wilma', 'pebbles', 'dino'])
    lol[5].extend(['betty', 'barney', 'bambam'])
    print 'lol: {}'.format(lol)
    assert(len(lol[0]) == 4)
    for l in lol[1:5]:
        assert(len(l) == 0)
    assert(len(lol[5]) == 3)

    assert(len(l6) == 3)
    assert l6 is lol[5]
    
    print 'yay'
    
    
