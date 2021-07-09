'''
Utility functions related to general-purpose python.
'''

import importlib


def lazy(fn):
    attr_name = '__lazy_' + fn.__name__

    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyprop


def import_class(fullname):
    ''' import and return a class based on module.clsname '''
    modname, clsname = tuple(fullname.rsplit('.', 1))
    mod = importlib.import_module(modname)
    return getattr(mod, clsname)


if __name__ == '__main__':
    def test_lazy():
        class Foo(object):
            @lazy
            def foo(self):
                print('calculating foo...')
                return 'foo'

        foo = Foo()
        print(dir(foo))
        print(foo.foo)
        print(dir(foo))
        print(foo.foo)
