import xarray as xr
import numpy as np
from shapely.geometry import Point
import json
import time
from tqdm import tqdm, trange
import os
import dask
import dask.dataframe as dd
import multiprocessing as mp
import argparse
from multiprocessing import Array
import concurrent.futures


# This class takes an argument of a filename that contains a .nc file
# and proceeds to average all data points for the entire year
class AverageNCData:
    
    def __init__(self, **kwargs):
        try:
            self.file = xr.open_dataset(kwargs['filename'], engine='netcdf4')
        except FileNotFoundError:
            print(kwargs['filename'])
            print("file not found")
        try:
            self.outfile=kwargs['outfile']
        except:
            print("Outfile not found. Please specify.  Refer to -h for help.")
            exit()
        self.data_variables = [i for i in self.file.data_vars]
        self.exempt_vars = ['Times', 'XLAT', 'XLONG', 'LAT', 'LON', 'LONG']
        self.get_times = len(self.file['Times'])
        self.num_lats = len(self.file['XLAT'])
        self.num_longs = len(self.file['XLONG'][0])
        self.final_arr = 0
        self.arr=0
        self.new_vars = {}
        self.set_new_vars()
        self.data_into_JSON()

    
    def set_new_vars(self):
        for i in self.data_variables:
            if(not self.exempt_vars.__contains__(i)):
                self.new_vars[i] =  self.average_variable(i)

    def average_variable(self, variable_name):
        print("Averaging " + str(variable_name))
        arr = self.file[variable_name]
        return np.average(arr, axis=0)
            
    def data_into_JSON(self):
        d = {}
        d["type"] = "FeatureCollection"
        d["features"] = []
        print("Converting to JSON")
        for i in trange(0, self.num_lats):
            for j in range(0, self.num_longs):
                lat = round(float(self.file['XLAT'][i][j]), 4)
                lon = round(float(self.file['XLONG'][i][j]), 4)
                dictionary = {  "type" : "Feature",
                    "geometry" :  Point(lon, lat).__geo_interface__,
                    "properties" :  self.get_data_at_point(i, j)}
                d["features"].append(dictionary)
            
        new_file = open(self.outfile, 'w')
        new_file.write(json.dumps(d))

    def get_data_at_point(self, i, j):
        d = {}
        for var in self.new_vars:
            d[str(var).lower()] = str(round(self.new_vars[var][i][j], 4))
        return d

     
def main():
    a = AverageNCData(filename='data/wrfout_d03_2012_fake.nc', outfile='data/out.geojson')
