def lazy(fn):
    attr_name = '__lazy_' + fn.__name__
    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyprop

if __name__ == '__main__':
    class Foo(object):
        @lazy
        def foo(self):
            print 'calculating foo...'
            return 'foo'

    foo = Foo()
    print dir(foo)
    print foo.foo
    print dir(foo)
    print foo.foo
