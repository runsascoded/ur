import json

class Loader:
    def __init__(self, load, save):
        self.load = load
        self.save = save

# class Loader:
#     def load(self, path, name, **_):
#         pass
#
#     def save(self, path, name, val, **_):
#         pass


class JSONLoader(Loader):
    @staticmethod
    def _load(path, **_):
        with path.open('r') as f:
            return json.load(f)

    @staticmethod
    def _save(path, val, **_):
        with path.open('w') as f:
            json.dump(val, f)

    def __init__(self):
        super(Loader, self).__init__(self, self._load, self._save)

JSON = JSONLoader()
