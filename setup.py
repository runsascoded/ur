from distutils.core import setup

setup(
      name='ur',
      packages=[ 'pclass', 'gists', ],
      version='0.1.0',
      description='Import remote Jupyter notebooks (or Python files)',
      author='Ryan Williams',
      author_email='ryan@runsascoded.com',
      py_modules=[ 'ur', 'cells', 'gist', 'regex', 'url_loader', ],
      install_requires=[ 'jupyter', 'nbformat==4.4.0', 'GitPython', 'lxml', 'cssselect', ],
      keywords=[ 'gists', 'imports', 'importlib', 'jupyter', 'notebooks', ],
      license='MIT',
      url='https://gitlab.com/runsascoded/ur',
)
