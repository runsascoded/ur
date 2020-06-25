#!/usr/bin/env python

from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_call as run


parser = ArgumentParser()
parser.add_argument('-i','--image',default='ur-test',help='Docker image name to build/use')
parser.add_argument('-w','--workdir',default='/ur',help='Working directory to mount the current dir into')
parser.add_argument('nb',help='Notebook to run')
args = parser.parse_args()
image = args.image
workdir = args.workdir
nb = args.nb

from runtests import build

build(image)
run([
    'docker', 'run',
    '-it',
    '-v',f'{Path.cwd()}:{workdir}',
    '--entrypoint', '/usr/local/bin/papermill',
    image,
    '-k', '3.8.2',
    nb, nb
])
