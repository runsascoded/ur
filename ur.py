import sys
from types import ModuleType

from url_loader import URLLoader


class UrModule(ModuleType):
    '''Wrap the module represented by this file
    
    Allows making it callable, and providing other syntactic sugar (like the `*` operator)
    '''
    def __init__(self, wrapped):
        super(UrModule, self).__init__(wrapped.__name__)
        self._wrapped = wrapped

    @property
    def skip_cache(self):
        import opts
        return opts.skip

    def __mul__(self, *args, **kwargs):
        return self(*(args + ('*',)), **kwargs)

    def __call__(self, *args, **kwargs):
        return self._wrapped.main(*args, **kwargs)

    def __getattr__(self, attr):
        return object.__getattribute__(self._wrapped, attr)


sys.modules[__name__] = UrModule(sys.modules[__name__])


# Instantiating this causes various `Importer`s to be injected into sys.meta_path
_loader = URLLoader()
def main(*args, **kwargs):
    '''This gets called by `UrModule.__call__` above'''
    ret = _loader.main(*args, **kwargs)
    return ret
