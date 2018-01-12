'''
Utility functions related to general-purpose python.
'''
import os
import importlib
from files import package_fileres
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
    def __init__(self, defaults_fn=None, def_section=None):
        self.defaults_fn = defaults_fn
        self.def_section = def_section
        

    def __call__(self, cls):
        clsname = cls.__name__  # shorthand
        config_fn = package_fileres(clsname.lower(), clsname.lower()+'.ini')

        # try to get default values from default config and section:
        if self.defaults_fn is not None and self.def_section is not None:
            if not os.path.isabs(self.defaults_fn):
                self.defaults_fn = package_fileres(clsname.lower(), self.defaults_fn)            
            def_config = get_config(self.defaults_fn)
            defaults = to_dict(def_config, self.def_section)
        else:
            defaults = {}
        cls_config = get_config(config_fn, defaults=defaults)

        load_attributes_from_config(cls, cls_config, clsname.lower())
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
