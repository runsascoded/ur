
from fnmatch import fnmatch

class UrIgnore:
    def __init__(self, node):
        self.node = node
        lines = node.read_lines()
        def parse(line):
            if line.startswith('!'):
                return dict(pattern=line[1:], include=True)
            else:
                return dict(pattern=line, include=False)
        lines = [
            parse(line)
            for line in lines
            if not line.startswith('#')
        ]
        self.lines = lines

    def check(self, node):
        include = True
        for line in self.lines:
            #pattern = f"{self.node.url.parent}/{line['pattern']}"
            pattern = f"*/{line['pattern']}"
            _include = line['include']
            match = fnmatch(node.url, pattern)
            #print(f'urignore {self.node}: pattern {pattern} vs. {node}: {bool(match)}')
            if match:
                #print(f'urignore {self.node}: pattern {pattern} vs. {node}: {_include}')
                if include != _include: include = _include

        return include

    def __str__(self): return f'UrIgnore({self.node})'
    def __repr__(self): return str(self)
