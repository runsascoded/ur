#!/usr/bin/env python

from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_call


def build(tag):
  check_call(['docker', 'build', '-f', 'Dockerfile.test', '-t', tag, '.'])


def run(image):
  check_call(['docker', 'run', image])


def main():
  parser = ArgumentParser()
  parser.add_argument('-t','--tag',default='ur-test',help='Docker image name to build/use')
  args = parser.parse_args()
  tag = args.tag

  build(tag)
  run(tag)


if __name__ == '__main__':
  main()
