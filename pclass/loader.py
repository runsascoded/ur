import json


class Loader:
    def __init__(self, load, save):
        self.load = load
        self.save = save


class JSONLoader(Loader):
    @staticmethod
    def _load(path):
        with path.open('r') as f:
            return json.load(f)

    @staticmethod
    def _save(path, val):
        with path.open('w') as f:
            json.dump(val, f)

    def __init__(self):
        super(JSONLoader, self).__init__(self._load, self._save)


JSON = JSONLoader()


noop = lambda path, val: None
