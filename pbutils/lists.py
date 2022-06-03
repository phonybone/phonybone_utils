''' Helper functions for lists '''


def grow(l, n, f):
    ''' extend a list by n elements; each element created by function f (no params) '''
    filler = [f() for _ in range(n)]
    l.extend(filler)


def grow_to(l, n, fill=None):
    ''' like grow(), but cap the length of the list at n elements '''
    amount = n - len(l)
    if amount > 0:
        grow(l, amount, fill)
    return l[n - 1]


def maxspan(spans):
    ''' given a list of spans (tuples), return the bounding span '''
    return (min([s[0] for s in spans]), max([s[1] for s in spans]))  # yes there are faster ways


def flatten(l):
    '''
    l is a list comprised of sub-lists or tuples.
    Return a 1D list containing all the elements of l in order.
    '''
    # see https://stackoverflow.com/questions/10632839/python-transform-list-of-tuples-in-to-1-flat-list-or-1-matrix
    return list(sum(l, ()))


def first_match(itr, match=lambda x: True, default=None):
    '''
    Return the first element of itr where match(elem) is True,
    or default if no match.
    '''
    return next((x for x in itr if match(x)), default)


def scale_list(L, max_L):
    ''' return a new list based on L by removing intermittent points '''
    N = len(L)
    n_remove = N - max_L
    i = max_L // 2
    new_L = list()
    # ratio = n_remove / N

    for idx in range(N):
        i += n_remove
        if i > N:
            i -= N
        else:
            new_L.append(L[idx])
    return new_L


if __name__ == '__main__':
    import sys

    def test_grow_to():
        lol = [[] for _ in range(3)]
        assert(len(lol) == 3)
        l6 = grow_to(lol, 6, list)
        print('lol: {}'.format(lol))
        print('l6: {}'.format(l6))
        assert(len(lol) == 6)
        assert(all(map(lambda l: type(l) is list, lol)))
        assert(len(l6) == 0)

        lol[0].extend(['fred', 'wilma', 'pebbles', 'dino'])
        lol[5].extend(['betty', 'barney', 'bambam'])
        print('lol: {}'.format(lol))
        assert(len(lol[0]) == 4)
        for l in lol[1:5]:
            assert(len(l) == 0)
        assert(len(lol[5]) == 3)

        assert(len(l6) == 3)
        assert l6 is lol[5]

    def test_first_match():
        itr = tuple(range(20))   # wrap in tuple() for immutability
        assert first_match(itr) == 0
        assert first_match(itr, lambda x: x & 1 == 0) == 0
        assert first_match(itr, lambda x: x & 1 == 1) == 1
        assert first_match(itr, lambda x: x == 13) == 13
        assert first_match(itr, lambda x: x == 34) is None
        assert first_match(itr, lambda x: x == 3, 'fred') == 3
        assert first_match(itr, lambda x: x == 34, 'fred') == 'fred'

    f = locals()[sys.argv[1]]
    args = sys.argv[2:]
    f(*args)
    print('yay')
