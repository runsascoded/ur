from distutils.core import setup

setup(name='ur',
      version='0.1.0',
      description='Import remote Jupyter notebooks (or Python files)',
      author='Ryan Williams',
      author_email='ryan@runsascoded.com',
      py_modules=[ 'ur', 'gist', 'gists', 'pclass', ],
      keywords=[ 'gists', 'imports', 'importlib', 'jupyter', 'notebooks', ],
      license='MIT',
      url='https://gitlab.com/runsascoded/ur',
)
