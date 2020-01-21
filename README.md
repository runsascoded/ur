# ur
import remote Python and Jupyter notebook files, from GitHub Gists, the local filesystem, or arbitrary URLs.

## Install:


```python
from sys import executable as python
!{python} -m pip install -q ur
```

## Import GitHub gists


```python
from gists._1288bff2f9e05394a94312010da267bb import *
a_b.a(), a_b.b(), c.c()
```




    ('aaa', 'bbb', 'ccc')



That imports 2 Jupyter notebooks from https://gist.github.com/1288bff2f9e05394a94312010da267bb (note the leading underscore in the `import` statement, which is necessary when the Gist ID begins with a number), and calls functions defined in them.

## Import arbitrary URLs
The `ur` module exposes a powerful API for importing code from {local,remote} {`.py`,`.ipynb`} files.

Here is an example directly importing one of the files in [the example gist used above](https://gist.github.com/ryan-williams/1288bff2f9e05394a94312010da267bb):


```python
import ur
a_b = ur('https://gist.githubusercontent.com/ryan-williams/1288bff2f9e05394a94312010da267bb/raw/a_b.ipynb')
a_b.a(), a_b.b()
```




    ('aaa', 'bbb')



### Import wildcards

In addition to calling the `ur` module (and returning a module), the `*` operator can be used:


```python
import ur
ur * 'https://gist.github.com/1288bff2f9e05394a94312010da267bb'
a_b.a(), a_b.b(), c.c()
```




    ('aaa', 'bbb', 'ccc')



This is is analogous to `import *` syntax, but can be used to import from arbitrary URLs (in this case, `ur` detects that the URL represents a gist, and imports the two `.ipynb` modules found there).

Here is an equivalent import using the `ur(…)` syntax:


```python
import ur
ur(gist='1288bff2f9e05394a94312010da267bb', all='*')
a_b.a(), a_b.b(), c.c()
```




    ('aaa', 'bbb', 'ccc')




```python
import ur
url = 'https://gist.githubusercontent.com/ryan-williams/1288bff2f9e05394a94312010da267bb/raw/0a2b5966c22c5461734063b78239262e39e4f363/c.ipynb'
ur(url, all=True)
c()
```




    'ccc'


