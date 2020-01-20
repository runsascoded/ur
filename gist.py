from subprocess import check_call
from tempfile import NamedTemporaryFile
from urllib.request import urlretrieve

from pclass.dircache import Meta
from pclass.field import field, directfield
from pclass.loader import load_xml
from git import Repo

from gist_url import GistURL


class File:
    def __init__(self, gist, path):
        self.gist = gist
        self.name = path.name
        self.path = path

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @property
    def module_name(self):
        return self.name.rpartition('.')[0]

    @property
    def url(self):
        gist = self.gist
        return f'https://gist.githubusercontent.com/{gist.user}/{gist.id}/raw/{self.name}'

    @property
    def web_url(self):
        gist = self.gist
        return f'https://gist.github.com/{gist.user}/{gist.id}#{gist.fragments[self.name]}'


class Gist(metaclass=Meta, debug=print):

    @property
    def git_url(self):
        return f'git@gist.github.com:{self.id}.git'

    @field
    def url(self):
        return f'https://gist.github.com/{self.id}'

    @field
    def user(self):
        root = self.xml
        [ author_link ] = root.cssselect('.author > a')
        return author_link.text

    @directfield
    def xml(self, path):
        urlretrieve(self.url, path)

    @xml.load
    def load_xml(self, path, **_):
        from lxml.etree import fromstring, XMLParser
        parser = XMLParser(recover=True)
        return fromstring(path.read_text(), parser)

    @field
    def author(self):
        return self.clone.active_branch.commit.author.email

    @directfield(parse=lambda path, **_: Repo(path))
    def clone(self, path):
        url = self.git_url
        print(f'Cloning {url} into {path}')
        check_call([ 'git', 'clone', url, str(path) ])

    @property
    def cloned_dir(self):
        return self._dir / 'clone'

    @property
    def files(self):
        return [ File(self, file) for file in self.cloned_dir.iterdir() ]

    @property
    def files_dict(self):
        return { file.name: file for file in self.files }

    @property
    def file_bases_dict(self):
        return { file.module_name: file for file in self.files }

    @field
    def fragments(self):
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

        return fragments
