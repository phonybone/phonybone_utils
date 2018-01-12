'''
Utility functions related to general-purpose python.
'''
import os
import importlib
import inspect
from files import package_fileres, replace_ext
from configs import get_config, load_attributes_from_config, to_dict

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

class configured_class(object):
    '''
    Decorator to set class attributes from a config section(s).
    With no parameters, looks for a config (.ini) file with the
    name <class>.ini, where <class> is the name of the class 
    (converted to lowercase). From within that config, it looks 
    for a section with the (exact) name of the class from which
    to initialize values.

    An addition config and section can be specified using the
    arguments to the decorator.  If given, it looks for file 
    relative to the class's package (unless the filename given
    is an absolute path) and uses the section specified.
    '''
    def __init__(self, defaults_fn=None, def_section=None):
        self.defaults_fn = defaults_fn
        self.def_section = def_section
        

    def __call__(self, cls):
        clsfile = inspect.getfile(cls)
        config_fn = replace_ext(os.path.basename(clsfile), 'ini')
        clsname = cls.__name__  # shorthand

        # try to get default values from default config and section:
        if self.defaults_fn is not None and self.def_section is not None:
            if not os.path.isabs(self.defaults_fn):
                modname, _ = os.path.splitext(os.path.basename(clsfile))
                self.defaults_fn = package_fileres(modname, self.defaults_fn)            
            def_config = get_config(self.defaults_fn)
            defaults = to_dict(def_config, self.def_section)
        else:
            defaults = {}
        cls_config = get_config(config_fn, defaults=defaults)

        load_attributes_from_config(cls, cls_config, clsname)
        return cls
        

if __name__ == '__main__':
    def test_lazy():
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
