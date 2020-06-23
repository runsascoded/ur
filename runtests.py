#!/usr/bin/env python

from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_call

def main():
  parser = ArgumentParser()
  args = parser.parse_args()

  check_call(['docker', 'build', '-f', 'Dockerfile.test', '-t', 'ur-test', '.'])
  check_call(['docker', 'run', 'ur-test'])

if __name__ == '__main__':
  main()