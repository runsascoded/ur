import sys
from types import ModuleType

from url_loader import URLLoader


class UrModule(ModuleType):

    def __init__(self, wrapped):
        super(UrModule, self).__init__(wrapped.__name__)
        self._wrapped = wrapped

    def __mul__(self, *args, **kwargs):
        return self(*(args + ('*',)), **kwargs)

    def __call__(self, *args, **kwargs):
        return self._wrapped.main(*args, **kwargs)

    def __getattr__(self, attr):
        return object.__getattribute__(self._wrapped, attr)


sys.modules[__name__] = UrModule(sys.modules[__name__])


_loader = URLLoader()
def main(*args, **kwargs):
    ret = _loader.main(*args, **kwargs)
    return ret
