"""
Allow for importing of IPython Notebooks as modules from Jupyter v4.

Updated from module collated here:
https://github.com/adrn/ipython/blob/master/examples/Notebook/Importing%20Notebooks.ipynb

Importing from a notebook is different from a module: because one
typically keeps many computations and tests besides exportable defs,
here we only run code which either defines a function or a class, or
imports code from other modules and notebooks. This behaviour can be
disabled by setting nbimporter.options['only_defs'] = False.

Furthermore, in order to provide per-notebook initialisation, if a
special function __nbinit__() is defined in the notebook, it will be
executed the first time an import statement is. This behaviour can be
disabled by setting nbimporter.options['run_nbinit'] = False.

Finally, you can set the encoding of the notebooks with
nbimporter.options['encoding']. The default is 'utf-8'.

Related reading:
- https://jupyter-notebook.readthedocs.io/en/stable/examples/Notebook/Importing%20Notebooks.html: example nb importer from jupyter docs
- https://github.com/adrn/ipython/blob/master/examples/Notebook/Importing%20Notebooks.ipynb: original source for jupyter example? (2014)

- https://github.com/grst/nbimporter: (this repo's base) wraps jupyter example, add cell-type filtering

- https://github.com/marella/nbimport: load from URL via %import magic

- https://github.com/rileyedmunds/import-ipynb: pip module from jupyter example code (2017)
- https://vispud.blogspot.com/2019/02/ipynb-import-another-ipynb-file.html mentions %run magic, which runs but doesn't import

- https://github.com/jupyter/notebook/issues/1588: jupyter discussing problem, points to example code, and ipython/ipynb repo
- https://github.com/ipython/ipynb: jupyter importer, supports cell-type restriction; obsolete? clumsy "ipynb.fs.full." import syntax

- https://github.com/jupyter/notebook/issues/3479: issue analyzing problem; recommends importnb
- https://github.com/deathbeds/importnb: jupyter importer / module-runner; similar to papermill?
"""

import ast
import os
import sys
from inspect import stack
from io import BytesIO
from re import match
from types import ModuleType
from urllib.parse import urlparse

import nbformat
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from requests import get as GET

from cells import CellDeleter
from gist_url import GistURL, chars, maybe
from notebooks import find_notebook


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


class URLLoader:

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def main(
        self,
        path=None,
        *names,
        encoding='utf-8',
        run_nbinit=True,
        only_defs=True,
        all=False,
        **kwargs,
    ):
        gist = kwargs.get('gist')
        github = kwargs.get('github')
        gitlab = kwargs.get('gitlab')
        tree = kwargs.get('tree')
        pkg = kwargs.get('pkg')
        file = kwargs.get('file')

        url = urlparse(path)
        if url.scheme:
            if match('^https?$', url.scheme):
                domain = url.netloc
                if domain == 'gist.github.com':

                    assert not gitlab
                    assert not pkg

                    kwargs_gist_url = None
                    if gist:
                        maybe_user = maybe(f'(?P<user>{chars})/')
                        id_re = f'(?P<id>{chars})'
                        m = match(gist, f'^{maybe_user}{id_re}$')
                        if not m:
                            raise Exception(f'Unrecognized gist: {gist}')

                        user = m.group('user')
                        id = m.group('id')

                        kwargs_gist_url = GistURL(id=id, user=user, tree=tree, file=file)

                    gist_url = GistURL.from_url_path(url.path, url.fragment)
                    print(f'gist_url: {gist_url}')
                    if kwargs_gist_url:
                        gist_url = gist_url.merge(kwargs_gist_url)
                        print(f'updated gist_url: {gist_url}')

                    raw_urls = gist_url.raw_urls()
                    print(f'raw_urls: {raw_urls}')
                    if not raw_urls:
                        raise Exception(f'No raw URLs found for gist {gist_url.url}')

                    if len(raw_urls) > 1:
                        raise NotImplementedError('Importing gists with multiple notebooks not supported… yet!')

                    [ raw_url ] = raw_urls
                    # Pass through to the rest of the function
                    path = raw_url
                    print(f'fwding on {raw_url}: {path}')

                elif domain == 'github.com':
                    raise NotImplementedError
                elif domain == 'gitlab.com':
                    raise NotImplementedError
                else:
                    pass
            else:
                raise Exception(f'Unsupported URL scheme: {url.scheme}')

        # load the notebook object
        nb_version = nbformat.version_info[0]

        if url.scheme:
            json = GET(path).content
            f = BytesIO(json)
            nb = nbformat.read(f, nb_version)
        else:
            with open(path, 'r', encoding=encoding) as f:
                nb = nbformat.read(f, nb_version)

        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = ModuleType(path)
        mod.__file__ = path
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython

        # Only do something if it's a python notebook
        if nb.metadata.kernelspec.language != 'python':
            return

        sys.modules[path] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            deleter = CellDeleter()
            for cell in filter(lambda c: c.cell_type == 'code', nb.cells):
                # transform the input into executable Python
                code = self.shell.input_transformer_manager.transform_cell(cell.source)
                if only_defs:
                    # Remove anything that isn't a def or a class
                    tree = deleter.generic_visit(ast.parse(code))
                else:
                    tree = ast.parse(code)
                # run the code in the module
                codeobj = compile(tree, filename=path, mode='exec')
                exec(codeobj, mod.__dict__)
        finally:
            self.shell.user_ns = save_user_ns

        # Run any initialisation if available, but only once
        if run_nbinit and '__nbinit_done__' not in mod.__dict__:
            if hasattr(mod, '__nbinit__'):
                mod.__nbinit__()
                mod.__nbinit_done__ = True

        if not names:
            return mod

        mod_dict = mod.__dict__
        if hasattr(mod, '__all__'):
            members = mod.__all__
        else:
            members = [ name for name in mod_dict if not name.startswith('_') ]

        import_all = '*' in names
        if import_all:
            names = [ name for name in names if not name == '*' ]

        not_found = list(set(names).difference(members))
        if not_found:
            raise Exception('Names not found: %s' % ','.join(not_found))

        if not import_all:
            members = names

        update = { name: mod_dict[name] for name in members }
        stk = stack()
        cur_file = stk[0].filename
        frame_info = next(frame for frame in stk if frame.filename != cur_file)
        frame_info.frame.f_globals.update(update)
        return mod


_loader = URLLoader()
def main(path, *names):
    ret = _loader.main(path, *names)
    return ret


class URLFinder(object):
    """Module finder that locates Jupyter Notebooks"""
    def __init__(self):
        self.loaders = {}

    def find_module(self, fullname, path=None):
        print(f'find_module: ${fullname}, ${path}')
        nb_path = find_notebook(fullname, path)
        if not nb_path:
            return

        key = path
        if path:
            # lists aren't hashable
            key = os.path.sep.join(path)

        if key not in self.loaders:
            self.loaders[key] = URLLoader(path)
        return self.loaders[key]


sys.meta_path.append(URLFinder())
