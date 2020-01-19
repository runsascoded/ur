import json
from os import environ as env
from pathlib import Path
from re import match
from subprocess import check_call
from tempfile import NamedTemporaryFile
from urllib.request import urlretrieve

import nbimporter
from cached_objs import Meta


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


class Gist(metaclass=Meta):

    @property
    def git_url(self):
        return GistCache.git_url(self.id)

    @property
    def url(self):
        return f'https://gist.github.com/{self.id}'

    @property
    def user(self):
        root = self.xml
        [ author_link ] = root.cssselect('.author > a')
        return author_link.text

    @property
    def xml(self):
        from lxml.etree import fromstring, XMLParser
        parser = XMLParser(recover=True)
        with NamedTemporaryFile() as f:
            urlretrieve(self.url, f.name)
            return fromstring(f.read(), parser)

    @property
    def author(self):
        return self.clone.active_branch.commit.author.email

    @property
    def clone(self):
        dest = self._dir / 'clone'
        check_call([ 'git', 'clone', self.git_url, str(dest) ])
        from git import Repo
        return Repo(dest)

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
