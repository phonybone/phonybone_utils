import os
import inspect
import pkg_resources as pr
from files import replace_ext
from configs import get_config, load_attributes_from_config, to_dict

class configured_class:
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
    def __init__(self, *args):
        if len(args) >= 2:
            args = list(args)
            self.defaults_fn = args.pop(0)
            self.def_sections = args
        else:
            self.defaults_fn = None
            self.def_sections = None

    def __call__(self, cls):
        # establish clsfile, pkg_root for cls:
        clsfile = inspect.getfile(cls)
        mod = inspect.getmodule(cls)
        pkg = mod.__name__.split('.')[0]
        pkg_root = os.path.abspath(pr.resource_filename(pkg, '.'))

        # try to get default values from default config and section:
        defaults = {
            '__class_file': clsfile,
            '__module': cls.__module__,
            '__pkg_root': pkg_root,
        }

        if self.defaults_fn is not None and self.def_sections is not None:
            if not os.path.isabs(self.defaults_fn):
                # locate defaults_fn in same directory as class file
                self.defaults_fn = os.path.join(os.path.dirname(clsfile), self.defaults_fn)
            else:
                # locate defaults_fn in package root, unless it already points to a real file:
                if not os.path.exists(self.defaults_fn):
                    self.defaults_fn = os.path.join(pkg_root, self.defaults_fn[1:])
            def_config = get_config(self.defaults_fn)
            for dsect in self.def_sections:
                defaults.update(to_dict(def_config, dsect))

        # get class config and inject values:
        config_fn = os.path.join(os.path.dirname(clsfile),
                                 replace_ext(os.path.basename(clsfile), 'ini'))
        cls_config = get_config(config_fn, defaults=defaults)
        load_attributes_from_config(cls, cls_config, cls.__name__)
        return cls


if __name__ == '__main__':
    with open('Fred.ini', 'w') as fred:
        print('this: that', file=fred)
        print('these: those', file=fred)
        print('them: they', file=fred)

    @configured_class('Fred.ini')
    class Fred:
        something = 'else'

    for thing in dir(Fred):
        print(F"Fred.{thing} = {getattr(Fred, thing)}")
