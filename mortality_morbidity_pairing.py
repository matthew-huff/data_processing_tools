import json
import csv
import xarray as xr
import numpy as np
from shapely.geometry import Point


def data_into_json(data_array):
    d = {}
    d["type"] = "FeatureCollection"
    d["features"] = []
    for i in data_array:
        #print(i)
        p = Point(i[1], i[0])
        dictionary = {  "type" : "Feature",
            "geometry" :  p.__geo_interface__, 
            "properties" : { "mortality" : np.round(i[2], 3)
                                ,
                              "lon" : p.x,
                              "lat" : p.y 
                              }
                               }
        d["features"].append(dictionary)
    print(d)
    return json.dumps(d)



def pair(netCDF_filename, csv_file_name):
    
    netCDF_file = xr.open_dataset(netCDF_filename, engine='netcdf4')
    lat_lon_array = np.empty((len(netCDF_file['XLAT']), len(netCDF_file['XLONG'][0])))
    mortality_array = np.empty((len(netCDF_file['XLAT']), len(netCDF_file['XLONG'][0])))
    print(lat_lon_array.shape)

    csv_file = open(csv_file_name, 'r')
    csvReader = csv.reader(csv_file)

    print(netCDF_file.variables)
    csvReader.__next__()
    for row in csvReader:
        if(float(row[6]) < 0.001):
            mortality_array[int(row[1])-1][int(row[0])-1] = 0
        else:
            mortality_array[int(row[1])-1][int(row[0])-1] = float(row[6])
            
    #data_array = np.empty( (len(netCDF_file['XLAT'])*len(netCDF_file['XLONG'], 3)) )
    data_array = []
    for i in range(0, len(netCDF_file['XLAT'])):
        for j in range(0, len(netCDF_file['XLONG'][0])):
            lat = netCDF_file['XLAT'][i][j]
            lon = netCDF_file['XLONG'][i][j]
            mort = mortality_array[i][j]

            data = [lat, lon, mort]
            data_array.append(data)

    out_json = data_into_json(data_array)
    outFile = open('data/out_mortality.geojson', 'w+')
    outFile.write(out_json)
    outFile.close()
    csv_file.close()










pair("data/wrfout_d03_2012_fake.nc", "data/BenMAP_LA100_WRFChem.CSV")


