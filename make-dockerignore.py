#!/usr/bin/env python

from subprocess import check_output as run

with open('.dockerignore','w') as f:
  f.write('*\n')
  f.write('!.git\n')
  f.flush()
  [
    f.write(f'!{line}\n')
    for line in
    run(['git','ls-files']).decode().split('\n')
    if line
  ]