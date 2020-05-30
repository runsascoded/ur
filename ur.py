import sys
from types import ModuleType

import opts
from url_loader import URLLoader


class UrModule(ModuleType):
    '''Wrap the module represented by this file

    Allows making it callable, and providing other syntactic sugar (like the `*` operator)
    '''
    def __init__(self, wrapped):
        super(UrModule, self).__init__(wrapped.__name__)

        # Dance around an infinite-recursing `__{get,set}attr__` loop here:
        K = '_wrapped'
        super(UrModule, self).__setattr__(K, wrapped)

    @property
    def skip_cache(self):
        import opts
        return opts.skip

    def __mul__(self, *args, **kwargs):
        return self(*(args + ('*',)), **kwargs)

    def __call__(self, *args, **kwargs):
        return self._wrapped.main(*args, **kwargs)

    def __getattr__(self, k):
        if hasattr(opts, k):
            return getattr(opts, k)
        return object.__getattribute__(self._wrapped, k)

    def __setattr__(self, k, v):
        if hasattr(opts, k):
            setattr(opts, k, v)
        return setattr(self._wrapped, k, v)

sys.modules[__name__] = UrModule(sys.modules[__name__])


# Instantiating this causes various `Importer`s to be injected into sys.meta_path
_loader = URLLoader()
def main(*args, **kwargs):
    '''This gets called by `UrModule.__call__` above'''
    ret = _loader.main(*args, **kwargs)
    return ret
