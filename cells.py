from ast import NodeTransformer

class CellDeleter(NodeTransformer):
    """ Removes all nodes from an AST which are not suitable
    for exporting out of a notebook. """
    def visit(self, node):
        """ Visit a node. """
        if node.__class__.__name__ in ['Module', 'FunctionDef', 'ClassDef',
                                       'Import', 'ImportFrom']:
            return node
        return None


