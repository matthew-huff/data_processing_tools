import os
import datetime
import json
import sys
import argparse
import kriging_data as kd
import time




parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filename',
    help='Pass a .geojson file to krig')
parser.add_argument('-sp', '--spacing', type=float, default=0.01,
    help='Spacing argument for spacing between data points at final kriging.  Smaller is better, but exponentially increases processing time')
parser.add_argument('-st', '--settimer', action='store_true',
    help='Use the -st tag to time various methods within the tool')
parser.add_argument('-c', '--chunks', type=int,
    help="number of chunks to split data into for preprocess kriging. Note: will create (c-1)^2 chunks, i.e. 4 will become 9 chunks.")

parser.add_argument('-fs', '--fast', action='store_true',
    help="Enable the fast tag for faster operation.  Less accurate, but much faster.")

parser.add_argument('-bo', 
    help="Specify a .geojson binning out file")
args = parser.parse_args()
args = vars(args)
print(args)
start = time.time()
d = kd.KrigingTool(filename=args['filename'], spacing=args['spacing'], settimer=args['settimer'], chunks=args['chunks'], fast=args['fast'], bo=args['bo'])

#x, y = d.limitGridToShape(0.01)
#a = d.krigingByShape(0.01, 1)

#print(a)
end = time.time()
print("Time to complete: " + str(end-start))