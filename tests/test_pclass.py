from pclass.dircache import Meta
from pclass.field import field

from pathlib import Path
from tempfile import TemporaryDirectory

def test_foo():
  with TemporaryDirectory() as cache_root:

    class Foo(metaclass=Meta, cache_root=cache_root):
      '''Example `Meta` class
      
      - instantiated with an `id`
      - offers a cached field `s` that is a duplicated string representation of the `id`
      '''
      count = 0
      @field
      def s(self):
        Foo.count += 1
        return str(self.id) * 2

    assert Foo.count == 0

    # Make a Foo, verify the field computation happens lazily (and Foo.count is incremented when it does)
    foo = Foo(4)
    assert Foo.count == 0

    assert foo.id == 4
    assert Foo.count == 0

    assert foo.s == '44'
    assert Foo.count == 1

    assert foo.s == '44'
    assert Foo.count == 1

    # Verify the state of the cache
    dir = Path(cache_root)
    [ class_dir ] = list(dir.iterdir())
    assert 'Foo' == class_dir.name
    [ foo_dir ] = list(class_dir.iterdir())
    assert '4' == foo_dir.name
    [ prop_file ] = list(foo_dir.iterdir())
    assert 's' == prop_file.name
    import json
    with prop_file.open('r') as f:
      assert json.load(f) == "44"

    # Instantiate a second Foo with the same ID (4)
    foo2 = Foo(4)
    assert foo is not foo2
    assert foo2.id == 4
    assert foo2.s == '44'
    # Verify that `s` was not recomputed:
    assert Foo.count == 1
    
    # Instantiate a third Foo with the same ID (4), but test cache-skipping
    foo3 = Foo(4, _skip_cache=True)
    assert foo is not foo2
    assert foo is not foo3
    assert foo3.id == 4
    assert foo3.s == '44'
    # Verify that `s` *was* recomputed:
    assert Foo.count == 2
