import json

from .loader import Loader, JSONLoader


def field(fn=None, loader=None, load=None, save=None):
    '''Decorator for class-fields that should be computed lazily and persistent-cached'''
    if fn:
        # this typically indicates argument-less invocation of the decorator; the field's default "getter" function is
        # passed as `fn`, and other fields are None
        return Field(fn, loader, load, save)
    else:
        # this indicates the decorator was invoked with non-`fn` keyword-args; a second level of invocation, with the
        # raw "getter" function, will occur, which we catch and bind `fn` during
        return lambda fn: Field(fn, loader, load, save)


class Field:
    '''Class encapsulating info about class-fields to be cached'''
    def __init__(self, compute, loader=None, load=None, save=None):
        self.compute = compute

        self.default_load = False
        self.default_save = False

        if not loader:
            loader = JSONLoader
            default_loader = True
        else:
            default_loader = False

        _load = loader.load
        _save = loader.save
        if load: _load = load
        if save: _save = save

        self.default_load = default_loader and not load
        self.default_save = default_loader and not save

        self.loader = Loader(_load, _save)
