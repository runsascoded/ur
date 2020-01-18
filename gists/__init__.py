import ast
import io
import sys
from tempfile import NamedTemporaryFile
from types import ModuleType
from urllib.parse import urlparse
from urllib.request import urlretrieve

import nbformat
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

from cells import CellDeleter

options = {'only_defs': True, 'run_nbinit': True, 'encoding': 'utf-8'}


class NBLoader(object):
    """ Module Loader for Jupyter Notebooks. """

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def load_module(self, fullname):
        """import a notebook as a module"""
        url = urlparse(fullname)
        print(f'load_module: {fullname} -> {url}')

        # load the notebook object
        nb_version = nbformat.version_info[0]

        if url.scheme:
            with NamedTemporaryFile() as f:
                print(f'Fetching {fullname} to {f.name}')
                urlretrieve(fullname, f.name)
                path = f.name
                with io.open(path, 'r', encoding=options['encoding']) as f:
                    nb = nbformat.read(f, nb_version)
                path = fullname
        else:
            path = find_notebook(fullname, self.path)
            with io.open(path, 'r', encoding=options['encoding']) as f:
                nb = nbformat.read(f, nb_version)

        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = ModuleType(fullname)
        mod.__file__ = path
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython

        # Only do something if it's a python notebook
        if nb.metadata.kernelspec.language != 'python':
            print("Ignoring '%s': not a python notebook." % path)
            return mod

        print("Importing Jupyter notebook from %s" % path)
        sys.modules[fullname] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            deleter = CellDeleter()
            for cell in filter(lambda c: c.cell_type == 'code', nb.cells):
                # transform the input into executable Python
                code = self.shell.input_transformer_manager.transform_cell(cell.source)
                if options['only_defs']:
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
        if options['run_nbinit'] and '__nbinit_done__' not in mod.__dict__:
            try:
                mod.__nbinit__()
                mod.__nbinit_done__ = True
            except (KeyError, AttributeError) as _:
                pass

        return mod


import ast
import html
import re
import sys
from importlib._bootstrap import spec_from_loader

from gist_cache import GistCache

import requests


class GistImporter:
    """
    `from stackoverflow import quick_sort` will go through the search results
    of `[python] quick sort` looking for the largest code block that doesn't
    syntax error in the highest voted answer from the highest voted question
    and return it as a module, or raise ImportError if there's no code at all.
    """
    API_URL = "https://api.stackexchange.com"

    def __init__(self, cache_path=None):
        self._cache = GistCache(cache_path)

    def find_spec(self, fullname, path=None, target=None):
        print(f'find_spec: {fullname} {path} {target}')
        path = fullname.split('.')
        assert path[0] == 'gists'
        id = path[1]
        if id.startswith('_'):
            id = id[1:]
        path = path[2:]
        gist = self._cache(id)
        url = gist.url

        if len(path) > 1:
            raise Exception(f'Too many path components for gist {id}: {path}')

        file = None
        if path:
            [ file ] = path

        if file:
        else:
            spec = spec_from_loader(fullname, self, origin=url, is_package=True)
            spec.submodule_search_locations = [ file.path for file in gist.files ]
            spec.__license__ = "CC BY-SA 3.0"
            spec._url = url
            spec.__author__ = gist.author
            return spec

    @classmethod
    def create_module(cls, spec):
        """Create a built-in module"""
        print(f'create_module {spec}')
        return spec

    @classmethod
    def exec_module(cls, module=None):
        """Exec a built-in module"""
        print(f'exec_module {module}')
        # try:
        #     exec(module._code, module.__dict__)
        # except:
        #     print(module._url)
        #     print(module._code)
        #     raise

    @classmethod
    def get_code(cls, fullname):
        return compile(cls._fetch_code(cls._fetch_url(fullname)), 'StackOverflow.com/' + fullname, 'exec')

    @classmethod
    def get_source(cls, fullname):
        return cls.get_code(fullname)

    @classmethod
    def is_package(cls, fullname):
        return False

    ############################

    @classmethod
    def _fetch_url(cls, query):
        query = query.lower().replace("stackoverflow.", "").replace("_", " ")
        ans = requests.get(cls.API_URL + "/search", {
            "order": "desc",
            "sort": "votes",
            "tagged": "python",
            "site": "stackoverflow",
            "intitle": query,
        }).json()
        if not ans["items"]:
            raise ImportError("Couldn't find any question matching `" + query + "`")
        return ans["items"][0]["link"]

    @classmethod
    def _fetch_code(cls, url):
        q = requests.get(url)
        return cls._find_code_in_html(q.text)

    @staticmethod
    def _find_code_in_html(s):
        answers = re.findall(r'<div id="answer-.*?</table', s, re.DOTALL)  # come get me, Zalgo

        def votecount(x):
            """
            Return the negative number of votes a question has.
            Might return the negative question id instead if its less than 100k. That's a feature.
            """
            r = int(re.search(r"\D(\d{1,5})\D", x).group(1))
            return -r

        for answer in sorted(answers, key=votecount):
            codez = re.finditer(r"<pre[^>]*>[^<]*<code[^>]*>((?:\s|[^<]|<span[^>]*>[^<]+</span>)*)</code></pre>", answer)
            codez = map(lambda x: x.group(1), codez)
            for code in sorted(codez, key=lambda x: -len(x)):  # more code is obviously better
                # don't forget attribution
                author = s
                author = author[author.find(code):]
                author = author[:author.find(">share<")]
                author = author[author.rfind('<a href="') + len('<a href="'):]
                author_link = author[:author.find('"'):]
                author_link = "https://stackoverflow.com" + author_link

                # fetch that code
                code = html.unescape(code)
                code = re.sub(r"<[^>]+>([^<]*)<[^>]*>", "\1", code)
                try:
                    ast.parse(code)
                    return code, author_link  # it compiled! uhm, parsed!
                except:
                    pass
        else:  # https://stackoverflow.com/questions/9979970/why-does-python-use-else-after-for-and-while-loops
            raise ImportError("This question ain't got no good code.")


sys.meta_path.append(GistImporter())
