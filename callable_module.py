from types import ModuleType

class CallableModule(ModuleType):

    def __init__(self, wrapped):
        super(CallableModule, self).__init__(wrapped.__name__)
        self._wrapped = wrapped

    def __mul__(self, *args, **kwargs):
        return self(*(args + ('*',)), **kwargs)

    def __call__(self, *args, **kwargs):
        return self._wrapped.main(*args, **kwargs)

    def __getattr__(self, attr):
        return object.__getattribute__(self._wrapped, attr)
