import ast
import sys
from inspect import stack
from pathlib import Path
from re import match
from types import ModuleType
from urllib.parse import urlparse

import nbformat
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

from cells import CellDeleter
from gist import Commit, File, Gist, chars
from gists import importer
from regex import maybe


def merge(l, r, *keys):
    l = l or {}
    n = l.copy()
    if not keys:
        keys = r.keys()
    for k in keys:
        if not k in r:
            continue
        rv = r[k]
        if k in l:
            lv = l[k]
            if lv != rv:
                raise Exception(f'Conflicting elem: {k} -> ({lv}, {rv})')
        else:
            n[k] = rv
    return n


class URLLoader:

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path
        self._print = None

    def print(self, *args, **kwargs):
        if self._print:
            self._print(*args, **kwargs)

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
        self.print(f'URLLoader.main({self}, path={path}, names={names}, all={all}, **{kwargs}')
        gist = kwargs.get('gist')
        github = kwargs.get('github')
        gitlab = kwargs.get('gitlab')
        pkg = kwargs.get('pkg')

        url = urlparse(path)
        if url.scheme or gist or github or gitlab:
            domain = url.netloc
            gist_attrs = Gist.parse_url(path, throw=False)
            if gist_attrs or gist:
                assert not github
                assert not gitlab
                assert not pkg

                gist_attrs = merge(gist_attrs, kwargs, 'user', 'commit', 'file')
                if gist:
                    maybe_user = maybe(f'(?P<user>{chars})/')
                    id_re = f'(?P<id>{chars})'
                    m = match(f'^{maybe_user}{id_re}$', gist)
                    if not m: raise Exception(f'Unrecognized gist: {gist}')

                    user = m.group('user')
                    id = m.group('id')

                    gist_attrs = merge(gist_attrs, dict(id=id, user=user))

                self.print(f'gist_attrs: {gist_attrs}')
                obj = Gist.from_dict(**gist_attrs)
                if isinstance(obj, Commit):
                    commit = obj
                    self.print(f'Parsed commit: {commit}')
                    gist = commit.gist
                    name = gist.module_name
                elif isinstance(obj, File):
                    file = obj
                    commit = file.commit
                    self.print(f'Parsed commit: {commit} (file {file})')
                    name = file.module_fullname
                else:
                    raise Exception(f'Unrecognized gist object: {obj}')

                if name in sys.modules:
                    mod = sys.modules[name]
                    self.print(f'Found loaded gist module: {mod}')
                else:
                    self.print(f'Loading gist module {name} (commit {commit})')
                    spec = importer.find_spec(name, commit=commit)
                    if not spec:
                        raise Exception(f'Failed to find spec for {name} (commit {commit})')

                    mod = importer.create_module(spec)
                    importer.exec_module(mod)

            elif domain == 'github.com':
                raise NotImplementedError
            elif domain == 'gitlab.com':
                raise NotImplementedError
            else:
                raise Exception(f'Unsupported URL: {path}')
        else:
            # load a local notebook
            nb_version = nbformat.version_info[0]
            with open(path, 'r', encoding=encoding) as f:
                nb = nbformat.read(f, nb_version)

            # create the module and add it to sys.modules
            mod = ModuleType(path)
            mod.__file__ = path
            mod.__loader__ = self
            mod.__dict__['get_ipython'] = get_ipython

            # Only do something if it's a python notebook
            if nb.metadata.kernelspec.language != 'python': return

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

        if not names and not all: return mod

        mod_dict = mod.__dict__

        if hasattr(mod, '__all__'):
            members = mod.__all__
        else:
            members = [ name for name in mod_dict if not name.startswith('_') ]

        import_all = '*' in names or all is True or all == '*'
        if import_all:
            names = [ name for name in names if not name == '*' ]

        not_found = list(set(names).difference(members))
        if not_found:
            raise Exception('Names not found: %s' % ','.join(not_found))

        if not import_all:
            members = names

        self.print(f'Bubbling up {members}')
        update = { name: mod_dict[name] for name in members }
        stk = stack()
        cur_file = stk[0].filename
        cur_dir = Path(cur_file).parent
        frame_info = next(frame for frame in stk if Path(frame.filename).parent != cur_dir)
        self.print(f'Frame: {frame_info}, {frame_info.filename}')
        frame_info.frame.f_globals.update(update)
        return mod

