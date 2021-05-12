from collections import defaultdict, Counter


def groupCount(it, f=None):
    ''' don't use this: use collections.Counter '''
    if f is None:
        def f(x):
            return x
    gc = Counter()
    for x in it:
        gc[f(x)] += 1
    return gc


def groupBy(it, f=None):
    '''
    You should really use itertools.groupby instead

    For a given iterator, return a dict that groups elements according to the function.
    Each key in the dict is the result of the function applied to the iterator's elements.
    Each value in the dict is a list of the grouped elements.
    If the function is None, then the key value is used as the function.
    '''
    if f is None:
        def f(x):
            return x
    gc = defaultdict(list)
    for x in it:
        gc[f(x)].append(x)
    return gc


def array2d(r, c):
    ''' create a 2d array of size r x c '''
    return [[None] * c for i in range(r)]


def arrayNd(*dims):
    '''
    Return N-dimensional array with dimensions defined by dims (len(dims) must make sense).
    '''
    if len(dims) == 2:
        return array2d(*dims)

    return [arrayNd(*dims[1:]) for _ in range(dims[0])]


########################################################################


if __name__ == '__main__':
    gc = groupCount(range(100), lambda x: x % 5)
    print(gc)

    gc = groupCount('this is a string with some duplicates in the string is a string some some this'.split(' '))
    print(gc)

    gc = groupBy(range(100), lambda x: x % 5)
    print(gc)

    gc = groupBy('this is a string with some duplicates in the string is a string some some this'.split(' '),
                 lambda s: len(s)
    )
    print(gc)
    print('yay')
