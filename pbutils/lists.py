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
    from strings import ppjson, qw
    def test_grow_to():
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

    def test_merge_overlapping():

        
        data = (
            ((1, 5), (4, 8)),
            ((23, 34), (43, 48), (48, 52), (51, 59), (62, 67)),
            ((23, 34),),
            ((1,3),(3,1)),
            ((3,4), (1,2)),
            ((3,4), (1,6)),
            )
        expected = (
            ((1, 8),),
            ((23, 34), (43, 59), (62, 67)),
            ((23, 34),),
            ((1,3),),
            ((1,2),(3,4)),
            ((1,6),),
        )
        for datum, exp_d in zip(data, expected):
            new_l = merge_overlapping(datum, ovlp, mrg)
            exp_d = set(exp_d)
            print ppjson('new_l: {}'.format(new_l))
            print ppjson('exp_d: {}'.format(exp_d))
            assert new_l == exp_d, "{} != {}".format(new_l, exp_d)
            print
    test_merge_overlapping()
    print 'yay'
    
    
