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
    # def __init__(self, defaults_fn=None, def_section=None):
    def __init__(self, *args):
        if len(args) == 1:
            raise TypeError('bad args: must be 0 or >2: {}'.format(args))
        if len(args) >= 2:
            args = list(args)
            self.defaults_fn = args.pop(0)
            self.def_sections = args
        else:
            self.defaults_fn = None
            self.def_sections = None

    def __call__(self, cls):
        clsfile = inspect.getfile(cls)

        # try to get default values from default config and section:
        defaults = {}
        if self.defaults_fn is not None and self.def_sections is not None:
            for dsect in self.def_sections:
                if not os.path.isabs(self.defaults_fn): # locate defaults_fn
                    self.defaults_fn = os.path.join(os.path.dirname(clsfile), self.defaults_fn)
                def_config = get_config(self.defaults_fn)
                defaults.update(to_dict(def_config, dsect))


        # get class config and inject values:
        config_fn = os.path.join(os.path.dirname(clsfile), replace_ext(os.path.basename(clsfile), 'ini'))
        cls_config = get_config(config_fn, defaults=defaults)
        load_attributes_from_config(cls, cls_config, cls.__name__)
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