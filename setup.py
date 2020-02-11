from setuptools import setup

with open('README.md', 'r') as f:
      long_description = f.read()

setup(
      name='ur',
      packages=[ 'pclass', 'gists', ],
      version='0.1.3',
      description='Import remote Jupyter notebooks (or Python files)',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Ryan Williams',
      author_email='ryan@runsascoded.com',
      py_modules=[ 'ur', 'cells', 'gist', 'regex', 'url_loader', ],
      install_requires=[ 'jupyter', 'nbformat==4.4.0', 'GitPython', 'lxml', 'cssselect', ],
      keywords=[ 'gists', 'imports', 'importlib', 'jupyter', 'notebooks', ],
      license='BSD',
      url='https://gitlab.com/runsascoded/ur',
      classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
      ],
      python_requires='>=3.3'
)
