from .loader import Loader, JSON


def field(fn=None, loader=None, **kwargs):
    '''Decorator for class-fields that should be computed lazily and persistent-cached'''
    if fn:
        # this typically indicates argument-less invocation of the decorator; the field's default "getter" function is
        # passed as `fn`, and other fields are None
        return Field(fn, loader, **kwargs)
    else:
        # this indicates the decorator was invoked with non-`fn` keyword-args; a second level of invocation, with the
        # raw "getter" function, will occur, which we catch and bind `fn` during
        return lambda fn: Field(fn, loader, **kwargs)


class Field:
    '''Class encapsulating info about class-fields to be cached'''
    def __init__(self, compute, loader=None, **kwargs):
        self.compute = compute

        self.default_load = False
        self.default_save = False

        if not loader:
            loader = JSON
            default_loader = True
        else:
            default_loader = False

        _load = loader.load
        _save = loader.save

        explicit_load = 'load' in kwargs
        explicit_save = 'save' in kwargs

        if explicit_load: _load = kwargs['load']
        if explicit_save: _save = kwargs['save']

        self.default_load = default_loader and not explicit_load
        self.default_save = default_loader and not explicit_save

        self.loader = Loader(_load, _save)


def directfield(download=None, parse=None):
    if not download:
        return lambda download: DirectField(download, parse)
    else:
        return DirectField(download, parse)


class DirectField:
    def __init__(self, download, parse=None):
        self.download = download
        self.parse = parse

    def load(self, fn):
        self.parse = fn
