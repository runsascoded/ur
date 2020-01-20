from functools import partial, wraps
from inspect import signature, _ParameterKind as Kind
from pathlib import Path

from .field import DirectField, Field
from .loader import Loader

class Meta(type):

    DEFAULT_CACHE_DIR = '.objs'

    def __new__(
        mcs, clsname, bases, dct,
        cache_root=None,
        cache_type_name=None,
        cache_key='id',
        cache_dir_key='_dir',
        debug=None,
        loader=None,
    ):
        '''Metaclass providing laziness and persistent caching for fields

        :param mcs: this metaclass
        :param clsname: the name of the class being instantiated
        :param bases: supertypes of the class being instantiated
        :param cache_root: top-level directory in which to create a subdirectory (with name given by `cache_type_name`)
               for all cached instances of the class being instantiated
        :param cache_type_name: subdirectory-name within `cache_root` for all caching pertaining to instances of the
               class being instantiated
        :param cache_key: name of a primary-key field that will be injected into the class, and used for lookups
        :param cache_dir_key: name of a field where the path to the object's cached fields on disk is stored
        :param debug: pass e.g. `print` here to enable debug-printing
        :param loader: default `Loader` to use for customizing serialization logic for `@field`s in this class

        Example:
        '''
        def print(*args, **kwargs):
            if debug:
                debug(*args, **kwargs)

        print(f'Meta.__new__({mcs}, {clsname}, {bases}, {dct})')
        methods = dct.copy()
        fields = []

        ### Cache initialization ###

        if not cache_root:
            cache_root = mcs.DEFAULT_CACHE_DIR

        cache_root = Path(cache_root).expanduser()

        if not cache_type_name:
            cache_type_name = clsname

        class_dir = cache_root / cache_type_name
        class_dir.mkdir(parents=True, exist_ok=True)
        print(f'Class cache dir: {class_dir}')

        ### Persisted/Cached/Lazy Field Handling ###
        # Look for methods annotated with `@field`, and munge them to:
        # - if present: load values (lazily, when accessed)) from the on-disk cache
        # - otherwise:
        #   - compute them (lazily, at access-time)
        #   - write them to the cache
        #   - save them in memory for future accesses
        #
        # Additionally:
        # - a new __init__ is synthesized (wrapping any user-provided __init__), which:
        #   - takes an "id" field (as a keyword-arg, or first positional argument):
        #     - used as a primary-key for each instance's cached fields
        #     - stored on the instance (as the "id" attr, by default; see `cache_key` above)
        #   - stores the cache-directory for the instance's cached fields (as "_dir" by default; see `cache_dir_key`
        #     above)
        # - a __str__ and __repr__ that display the "primary key" ("id") field as well as any cached fields that have
        #   been computed/accessed

        for name, member in dct.items():
            print(f'Checking: {name}: {member}')

            def _bind(fn, name, **_kw):
                kw = _kw.copy()
                params = signature(fn).parameters
                print(f'{name} params: {params} for fn {fn}')
                if 'name' in params:
                    print(f'{name} adding name {name} to {fn}')
                    kw['name'] = name

                has_kwargs = Kind.VAR_KEYWORD in [ param.kind for param in params.values() ]

                def wrapped(self, path, name, **_kw):
                    if cache_key in params or has_kwargs:
                        print(f'{name} adding {cache_key} to {fn}')
                        kw[cache_key] = getattr(self, cache_key)
                    if 'path' in params or has_kwargs:
                        print(f'{name} adding path {path} to {fn}')
                        kw['path'] = path
                    if 'self' in params:
                        print(f'{name} adding self {self} to {fn}')
                        kw['self'] = self

                    print(f'{name}: calling {fn} with {kw}')
                    return fn(**_kw, **kw)

                return partial(wrapped, name=name)

            bind = partial(_bind, name=name)
            print(f'{name}: bind {bind} {signature(bind).parameters}')

            if isinstance(member, Field):
                field = member
                print(f'field: {name} -> {field}')
                fields.append(name)
                _name = f'_{name}'

                # If the class provides a default loader, use its load/save methods on fields that didn't explicitly set
                # their own
                _loader = field.loader
                _loader = Loader(_loader.load, _loader.save)
                if loader and field.default_load: _loader.load = loader.load
                if loader and field.default_save: _loader.save = loader.save

                def wrapped_fn(self, name, _name, field, loader):
                    '''Synthetic "getter" for a `Field` member of a class.

                    Replaces the user-provided getter (`field.compute`), wrapping it in caching/persistence logic.

                    :param self: class instance containing fields to cache
                    :param name: name of the `Field` being instrumented
                    :param _name: slot in which to store the computed value of this field (when present; typically just
                                  the field's `name` with an underscore prefixed)
                    :param field: `Field` instance being instrumented
                    :param loader: Serializer between in-memory and disk-cache reprs
                    :return: the value of this `Field` on the `self` class instance (whether loaded from cache or
                             computed + saved to cache)
                    '''
                    print(f'wrapped_fn: {name} ({_name}): field {field} loader {loader}')
                    if not hasattr(self, _name):
                        # This field's value hasn't been loaded or computed on this instance yet

                        # Path to cache this instance's fields to
                        cache_dir = getattr(self, cache_dir_key)

                        # Path to cache this specific field to (within the instance's dir)
                        path = cache_dir / name

                        # Misc kwargs passed to the serialization layer, to enable various customizations
                        # kw = {}
                        # kw[cache_key] = getattr(self, cache_key)
                        # kw['name'] = name

                        if path.exists():
                            # Load from cache
                            load = bind(loader.load)
                            val = load(self, path)
                            #val = loader.load(path, **kw)
                            print(f'Loaded attr from cache: {_name}={val}')
                        else:
                            print(f'Computing: {name}')

                            # Compute the field's value
                            val = field.compute(self)
                            print(f'Computed: {name}={val}')

                            cache_dir.mkdir(parents=True, exist_ok=True)

                            print(f'Saving {name} to {path}')
                            save = loader.save
                            if save:
                                save = bind(save)
                                save(self, path, val=val)
                            # if save: loader.save(path, val, **kw)

                        # set loaded/computed value on `self` instance
                        setattr(self, _name, val)
                    else:
                        print(f'Lookup: {name}={getattr(self, _name)}')

                    return getattr(self, _name)

                # Partially apply all relevant fields (ensures closures are bound properly)
                applied = partial(wrapped_fn, name=name, _name=_name, field=field, loader=_loader)

                # A `@property` is ultimately returned, for parend-less call-site syntactic-sugar
                prop = property(applied)

                # Store the modified field getter on the class' definition
                print(f'Setting method: {name}: {prop}')
                methods[name] = prop
            elif isinstance(member, DirectField):
                field = member
                print(f'field: {name} -> {field}')
                fields.append(name)
                _name = f'_{name}'

                # If the class provides a default loader, use its load/save methods on fields that didn't explicitly set
                # their own
                # _loader = field.loader
                # _loader = Loader(_loader.load, _loader.save)
                # if loader and field.default_load: _loader.load = loader.load
                # if loader and field.default_save: _loader.save = loader.save

                def wrapped_fn(self, name, _name, field):
                    '''Synthetic "getter" for a `Field` member of a class.

                    Replaces the user-provided getter (`field.compute`), wrapping it in caching/persistence logic.

                    :param self: class instance containing fields to cache
                    :param name: name of the `Field` being instrumented
                    :param _name: slot in which to store the computed value of this field (when present; typically just
                                  the field's `name` with an underscore prefixed)
                    :param field: `Field` instance being instrumented
                    :return: the value of this `Field` on the `self` class instance (whether loaded from cache or
                             computed + saved to cache)
                    '''
                    print(f'wrapped_fn: {name} ({_name}): field {field}')
                    if not hasattr(self, _name):
                        # This field's value hasn't been loaded or computed on this instance yet

                        # Path to cache this instance's fields to
                        cache_dir = getattr(self, cache_dir_key)

                        # Path to cache this specific field to (within the instance's dir)
                        path = cache_dir / name

                        # Misc kwargs passed to the serialization layer, to enable various customizations
                        # kw = {}
                        # kw[cache_key] = getattr(self, cache_key)
                        # kw['name'] = name

                        if not path.exists():
                            print(f'Downloading: {name}')

                            cache_dir.mkdir(parents=True, exist_ok=True)

                            # Compute the field's value
                            download = bind(field.download)
                            download(self, path)
                            # field.download(self, path, **kw)
                            print(f'Downloaded to {path}')

                        # Load from cache
                        parse = bind(field.parse)
                        val = parse(self, path)
                        # val = field.parse(path, **kw)
                        print(f'Loaded attr from cache: {_name}={val}')

                        # set loaded/computed value on `self` instance
                        setattr(self, _name, val)
                    else:
                        print(f'Lookup: {name}={getattr(self, _name)}')

                    return getattr(self, _name)

                # Partially apply all relevant fields (ensures closures are bound properly)
                applied = partial(wrapped_fn, name=name, _name=_name, field=field)

                # A `@property` is ultimately returned, for parend-less call-site syntactic-sugar
                prop = property(applied)

                # Store the modified field getter on the class' definition
                print(f'Setting method: {name}: {prop}')
                methods[name] = prop
            else:
                print(f'Skipping: {name}')

        # List of fields that were instrumented
        print(f'Fields: {fields}')

        orig_init = None
        if '__init__' in methods:
            orig_init = methods['__init__']

        def __init__(self, *args, **_kwargs):
            '''Auto-generated constructor that injects a primary-key argument, and sets a field-cache directory'''
            kwargs = _kwargs.copy()
            print(f'__init__(self, {args}, {kwargs})')

            if cache_key in kwargs:
                cache_id = kwargs.pop(cache_key)
            elif args:
                cache_id = args[0]
                args = args[1:]
            else:
                raise Exception(f"Couldn't find {cache_key} field in kwargs or as first element of *args ")

            print(f'Setting cache id {cache_key}={cache_id}')
            setattr(self, cache_key, cache_id)

            cache_dir = class_dir / str(cache_id)
            setattr(self, cache_dir_key, cache_dir)
            print(f'Set {cache_dir_key}={cache_dir} for id {cache_id}')

            if orig_init:
                orig_init(self, *args, **kwargs)

            print(f'Done with injected __init__')

        methods['__init__'] = wraps(orig_init)(__init__) if orig_init else __init__

        def __str__(self):
            '''Convenient str/repr helper showing an instance's cache-primary-key and any materialized fields'''
            strs = [ f'{cache_key}={getattr(self, cache_key)}' ]
            for field in fields:
                k = f'_{field}'
                if hasattr(self, k):
                    v = getattr(self, k)
                    strs.append(f'{field}={v}')
            return '%s(%s)' % (clsname, ', '.join(strs))

        if '__str__' not in methods:
            methods['__str__'] = __str__

        if '__repr__' not in methods:
            methods['__repr__'] = __str__

        new = super(Meta, mcs).__new__(mcs, clsname, bases, methods)
        print(f'returning {new}: {methods}')

        return new
