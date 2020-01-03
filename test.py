import ur
ur('https://gist.githubusercontent.com/ryan-williams/58d781f4ea97e98ee80e6c4af0c8acf3/raw/458a253b9afececff0a6ba11d40b7f79f88ec151/test_nb.ipynb', '*')
print('globals: %s' % ' '.join(globals().keys()))
print(globals()['foo'])
print(foo())
