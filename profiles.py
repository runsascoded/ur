#!/usr/bin/env python

from argparse import ArgumentParser
import pstats


parser = ArgumentParser()
parser.add_argument('-s','--sort',default='time')
parser.add_argument('-c','--callers',action='store_true')
parser.add_argument('-C','--callees',action='store_true')
parser.add_argument('-D','--no-dirs',action='store_true')
parser.add_argument('-n','--num',type=int,default=50)
parser.add_argument('file')
args = parser.parse_args()


p = pstats.Stats(args.file)

if args.no_dirs:
    p = p.strip_dirs()

p.sort_stats(args.sort)

if args.callers:
    p.print_callers(args.num)
elif args.callees:
    p.print_callees(args.num)
else:
    p.print_stats(args.num)
