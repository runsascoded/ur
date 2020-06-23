
import git
from pathlib import Path
from urlpath import URL

class Node:
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], Node): return args[0]
        return super(Node, cls).__new__(cls)

    def __repr__(self): return str(self)
    def read(self): pass
    def read_text(self): return self.read().decode()
    def read_lines(self, nonempty=True):
        lines = [
            line.rstrip('\n')
            for line in
            self.read_text().split('\n')
        ]

        if nonempty:
            lines = [ line for line in lines if line ]

        return lines

class PathNode(Node):
    def __init__(self, path):
        if isinstance(path, Node): return
        self.path = Path(path)
        self.name = self.path.name
        self.url = URL(path)

    @property
    def is_file(self): return self.path.is_file()

    @property
    def is_dir(self): return self.path.is_dir()

    @property
    def exists(self): return self.path.exists()

    @property
    def children(self):
        children = list(self.path.iterdir())
        return { p.name: PathNode(p) for p in children }

    def read(self):
        assert self.is_file
        with self.path.open('rb') as f:
            return f.read()

    def __str__(self): return f'Node({self.path})'


class GitNode(Node):
    def __init__(self, obj, url=None):
        if isinstance(obj, Node): return
        from git import Blob, Tree
        import _github, _gist
        if isinstance(obj, (_github.Commit, _gist.Commit)):
            tree = obj.commit.tree
            self.url = URL(obj.www_url)
            obj = tree
        elif not url:
            raise ValueError(f'No URL passed')
        else:
            self.url = url

        self.obj = obj
        self.is_file = isinstance(obj, Blob)
        self.is_dir = isinstance(obj, Tree)
        self.name = obj.name

    @property
    def children(self):
        if self.is_file: return None
        blobs = self.obj.blobs
        trees = self.obj.trees
        return {
            obj.name: GitNode(obj, self.url / obj.name)
            for obj in (blobs + trees)
        }

    def read(self):
        assert self.is_file
        return self.obj.data_stream.read()

    def __str__(self): return f'Node({self.url})'
