from collections import defaultdict


def groupCount(it, f=None):
    if f is None:
        def f(x):
            return x
    gc = defaultdict(int)
    for x in it:
        gc[f(x)] += 1
    return gc


def groupBy(it, f=None):
    if f is None:
        def f(x):
            return x
    gc = defaultdict(list)
    for x in it:
        gc[f(x)].append(x)
    return gc

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
