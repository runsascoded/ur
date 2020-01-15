import sys

from ur import find_notebook
from url_loader import URLLoader


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
