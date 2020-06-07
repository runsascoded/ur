
import git
from pathlib import Path

class Node:
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], Node): return args[0]
        return super(Node, cls).__new__(cls)

    def __repr__(self): return str(self)
    def read(self): pass
    def read_text(self): return self.read().decode()

class PathNode(Node):
    def __init__(self, path):
        if isinstance(path, Node): return
        self.path = Path(path)
        self.name = self.path.name

    @property
    def is_file(self): return self.path.is_file()

    @property
    def is_dir(self): return self.path.is_dir()

    @property
    def children(self):
        return { p.name: PathNode(p) for p in self.path.iterdir() }

    def read(self):
        assert self.is_file
        with self.path.open('rb') as f:
            return f.read()

    def __str__(self): return f'Node({self.path})'


class GitNode(Node):
    def __init__(self, obj):
        if isinstance(obj, Node): return
        from git import Blob, Commit, Tree
        if isinstance(obj, Commit):
            obj = obj.tree

        self.obj = obj
        self.is_file = isinstance(obj, Blob)
        self.is_dir = isinstance(obj, Tree)
        self.name = obj.name

    @property
    def children(self):
        if self.is_file: return None
        blobs = self.obj.blobs
        trees = self.obj.trees
        return { obj.name: obj for obj in (blobs + trees) }

    def read(self):
        assert self.is_file
        return self.obj.data_stream.read()

    def __str__(self): return f'Node({self.obj})'
