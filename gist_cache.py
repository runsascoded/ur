import json
from os import environ as env
from pathlib import Path
from re import match
from subprocess import check_call
from tempfile import NamedTemporaryFile
from urllib.request import urlretrieve

from gist_url import GistURL
from gist_url import chars, hexs


class File:
    def __init__(self, gist, path):
        self.gist = gist
        self.name = path.name
        self.path = path
        self._contents = None

    @property
    def contents(self):
        if not self._contents:
            self._contents = self.path.read_text()
        return self._contents

    def __str__(self):
        return self.name

    def url(self):
        return f'https://gist.githubusercontent.com/{self.gist.user}/{self.gist.id}/raw/{self.name}'

    def web_url(self):
        return f'https://gist.github.com/{self.gist.user}/{self.gist.id}#file-a_b-ipynb'


class Gist:
    def __init__(self, id, user=None, author=None, dir=None, xml=None, fragments=None, cache=None):
        m = match(f'^(?P<user>{chars})/(?P<id>{hexs})$', id)
        if m:
            matches = m.groupdict()
            u = matches['user']
            assert user is None or (user == matches['user']), f'{user} ⟹ ({user} == {u})'
            user = u
            id = matches['id']

        self.id = id

        self.cache = None
        if isinstance(cache, GistCache)
            self.cache = cache
        else:
            self.cache = GistCache.get(cache)

        self._dir = self.cache.path(self.id)

        self._author = author
        self._fragments = fragments
        self._user = user
        self._xml = xml
        self._files = None

    def clone_dir(self):
        return self._dir / 'clone'

    @classmethod
    def load(cls, dir, cache):
        id = dir.name

        xml = None
        xml_path = dir / 'xml'
        if xml_path.exists():
            from lxml.etree import fromstring, XMLParser
            parser = XMLParser(recover=True)
            with xml_path.open('r') as f:
                xml = fromstring(f.read(), parser)

        kwargs = {}
        for k in [
            'author',
            'user',
            'fragments',
            'xml',
        ]:
            path = dir / k
            if path.exists():
                with path.open('r') as f:
                    if k == 'xml':
                        from lxml.etree import fromstring, XMLParser
                        parser = XMLParser(recover=True)
                        kwargs[k] = fromstring(f.read(), parser)
                    else:
                        kwargs[k] = json.load(f)

        return Gist(id, dir=dir, cache=cache, **kwargs)

    @property
    def git_url(self):
        return GistCache.git_url(self.id)

    @property
    def url(self):
        return f'https://gist.github.com/{self.id}'

    @property
    def user(self):
        if not self._user:
            root = self.xml
            [ author_link ] = root.cssselect('.author > a')
            self._user = author_link.text
        return self._user

    @property
    def xml(self):
        if not self._xml:
            from lxml.etree import fromstring, XMLParser
            parser = XMLParser(recover=True)
            with NamedTemporaryFile() as f:
                urlretrieve(self.url, f.name)
                self._xml = fromstring(f.read(), parser)
        return self._xml

    @property
    def author(self):
        if not self._author:
            cloned_dir = self.cloned_dir
            from git import Repo
            repo = Repo(cloned_dir)
            self.cache.path(self.id)
            self._author = repo.active_branch.commit.author.email
        return self._author

    @property
    def cloned_dir(self):
        if not self._dir:
            self.cache(self.id)
            self._dir = self.cache.path(self.id)

        return self._dir

    @property
    def files(self):
        if not self._files:
            cloned_dir = self.cloned_dir
            self._files = [ File(file) for file in cloned_dir.iterdir() ]
        return self._files

    @property
    def files_dict(self):
        return { file.name: file for file in self.files }

    @property
    def fragments(self):
        if not self._fragments:
            root = self.xml
            file_elems = root.cssselect('.file')
            fragments = {}
            for f in file_elems:
                [ raw_a ] = f.xpath('.//a[contains(., "Raw")]')
                raw_url_path = raw_a.attrib['href']
                gist_url = GistURL.from_full_raw_url_path(raw_url_path)

                [ link ] = f.cssselect('.file-info > .css-truncate')
                fragment = link.attrib['href']
                if not fragment.startswith('#'):
                    raise Exception(f'Expected file header for {gist_url.file} to be an intra-page fragment link; found {fragment}')
                fragment = fragment[1:]

                fragments[gist_url.file] = fragment

            self._fragments = fragments

        return self._fragments


class GistCache:
    CACHE_PATH_ENV_VAR = 'GIST_CACHE_PATH'
    DEFAULT_CACHE_PATH = '.gists'

    CACHES = {}

    def __init__(self, path=None):
        path = self.resolve(path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        if path in self.CACHES:
            raise Exception(f"Can't instantiate another cache pointing at {path}")

        self.CACHES[path] = self
        self._path = path

        gists = {}
        self.gists = gists

        for child in path.iterdir():
            self._load_gist(child)

    @classmethod
    def resolve(cls, path):
        if cls.CACHE_PATH_ENV_VAR in env:
            path = env[cls.CACHE_PATH_ENV_VAR]
        else:
            path = Path.home() / cls.DEFAULT_CACHE_PATH

        return Path(path).resolve().absolute()

    @classmethod
    def get(cls, path):
        path = cls.resolve(path)
        if path in cls.CACHES:
            return cls.CACHES[path]

        return GistCache(path)

    def _load_gist(self, path):
        return Gist.load(path, cache=self)

    def path(self, id):
        return self._path / id

    @classmethod
    def git_url(cls, id):
        return f'git@gist.github.com:{id}.git'

    def __call__(self, id):
        if id not in self.gists:
            gist = Gist(id, cache=self)
            self.gists[id] = gist
        return self.gists[id]
