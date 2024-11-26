'''
Utility functions related to general-purpose python.
'''
import sys
import importlib
import operator as op


def require_python(version, opname=None):
    if isinstance(version, str):
        version = version.split('.')
    if not isinstance(version, (tuple, list)) or len(version) != 3:
        raise ValueError(F"bad version format: {version}")
    version = tuple(version)    # in case of list
    
    if opname is None:
        opname = 'eq'
    else:
        opnames = {
            '==': 'eq',
            '>=': 'le',
            '>': 'lt',
            '<': 'gt',
            '<=': 'ge'
        }
        opname = opnames.get(opname, opname)

    op = getattr(op, opnames)

    sysver = (sys.version_info.major,
              sys.version_info.minor,
              sys.version_info.micro)
    return op(vesion, sysver)
        

def lazy(fn):
    attr_name = '__lazy_' + fn.__name__

    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyprop


def import_class(fullname):
    ''' import and return a module and class based on module.clsname '''
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
