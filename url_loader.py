import ast
from inspect import stack
from io import BytesIO
from pathlib import Path
from re import match
import sys
from types import ModuleType
from urllib.parse import urlparse

import nbformat
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from requests import get as GET

from cells import CellDeleter
from gist_url import GistURL, chars, maybe


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
        print(f'URLLoader.main({self}, path={path}, names={names}, all={all}, **{kwargs}')
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
        cur_dir = Path(cur_file).parent
        frame_info = next(frame for frame in stk if Path(frame.filename).parent != cur_dir)
        frame_info.frame.f_globals.update(update)
        return mod

