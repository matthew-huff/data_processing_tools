import pykrige.kriging_tools as kt
from pykrige.ok import OrdinaryKriging
import time
import datetime
import shapely
import json
import numpy as np
from shapely.geometry import MultiPoint, Point, box
from shapely.strtree import STRtree
import matplotlib.pyplot as plt
from shapely.wkt import loads
from tqdm import tqdm, trange


import shapefile
import geopandas as gpd
import DataIntoJSON as dj


class KrigingTool:

    def __init__(self, **kwargs):
        
        
        with open(kwargs['filename'], 'r') as json_file:
            json_string = json_file.read()
        self.json_reader = json.loads(json_string)
        
        try:
            with open(kwargs['filename'], 'r') as json_file:
                json_string = json_file.read()
            self.json_reader = json.loads(json_string)
            
            
        except:
            print("Error: Input a filename")
            exit()

        try: 
            self.binned_out = kwargs['bo']
            self.binned_out_part = self.binned_out[:-8] + "_part.geojson"

        except:
            print("Error: specify binned out data file with .geojson end")

        try:
            self.chunks = kwargs['chunks']
        except:
            self.chunks = 1
        self.f=kwargs['fast']
        self.st = kwargs['settimer']
        self.num_vars = 0
        self.county_boundary = shapefile.Reader('data/LA_County_City_Boundaries.shp')
        self.ct = gpd.read_file("data/census_tracts.geojson")
        self.main()
        
    #Returns a dictionary of { lats, lons, variables }.  Each contain an array in with points in order sharing the same index.
    # The variables array at point i contains a dictionary of all the different variables and their values
    def construct_dataset_from_geojson(self):
        lats = []
        lons = []
        variables = []
        #point_checker = pc.PointChecker()
        for i in self.json_reader['features']:
            lon = i['geometry']['coordinates'][0]
            lat = i['geometry']['coordinates'][1]
            if(self.check_if_point_within_bounds(lon, lat)):
                lons.append(lon)
                lats.append(lat)
                varDict = {}
                for j in i['properties']:
                    varDict[j] = i['properties'][j]
                variables.append(varDict)

                if(self.num_vars == 0):
                    self.num_vars = len(varDict)

        geo_data={  
                    'lats' : lats,
                    'lons' : lons,
                    'variables' : variables
                }
        return geo_data

    def check_if_point_within_bounds(self, x, y):
        p = Point(x, y)
        #print(self.county_boundary.bbox)
        b = box(
            self.county_boundary.bbox[0],
            self.county_boundary.bbox[1],
            self.county_boundary.bbox[2],
            self.county_boundary.bbox[3])
        return b.contains(p)

    def perform_kriging(self, data, grid_x, grid_y):
        startTime = time.time()
        OK = OrdinaryKriging(data[:,0], data[:,1], data[:,2], variogram_model='linear', verbose=False, enable_plotting=False)
        z, ss = OK.execute('grid', grid_x, grid_y)
        endTime = time.time()
        if(self.st):
            print("performKriging Method took {:.2f} seconds".format(endTime-startTime))
        return z


    #Expects return data from construct_dataset_from_geojson
    def create_point_hashtable(self, geo_data):
        lats = geo_data['lats']
        lons = geo_data['lons']
        variables = geo_data['variables']
        hash_table = {}
        for i in range(len(lats)):
            index = str(lats[i]) + str(lons[i]) 
            hash_table[index] = variables[i]

        return hash_table

    #Expecting return data from construct_dataset_from_geojson
    def create_MultiPoint(self, geo_data):
        points = []
        lats = geo_data['lats']
        lons = geo_data['lons']
        
        for i in range(len(lats)):
            p = Point(lats[i], lons[i])
            points.append(p)
        MP = MultiPoint(points)
        
        return MP

    
    def create_chunk_boxes(self, MP):
        
        xmin = MP.bounds[0]
        ymin = MP.bounds[1]
        xmax = MP.bounds[2]
        ymax = MP.bounds[3]
        

        xsplit = np.linspace(xmin, xmax, self.chunks)
        ysplit = np.linspace(ymin, ymax, self.chunks)
  

        boxes = []
        #Create a set of boxes to represent chunks within the space.
        for i in range(0, self.chunks-1):
            for j in range(0, self.chunks-1):
                b = box(xsplit[i], ysplit[j], xsplit[i+1], ysplit[j+1])
                boxes.append(b)
        return boxes

    #Takes a multipoint set and a list of chunk 'boxes' and creates an array pt_chunks
    # of size len(boxes), where each pt_chunks[i] is an array of all points that fall within the box
    # at boxes[i]
    def split_points_into_chunks(self, MP, boxes):
        tree = STRtree(MP)
        pt_chunks = []
        for b in boxes:
            query_geom = b
            pts = [o.wkt for o in tree.query(query_geom)]
            pt_chunks.append(pts)

        return pt_chunks
            
    def main(self):
        self.fast_kriging()
        
    
    def fast_kriging(self):
        
        geo_data = self.construct_dataset_from_geojson()
        variables = geo_data['variables'][0]
        krigged_variable_dict = {}  #Dictionary to hold points and variables of data that is krigged
        nonkrigged_variable_dict = {} #Dictionary to hold points and variables of data that is not krigged

        #Create an array of centroid points called pts of census tracts from the census tract .shp fle
        geometries = [i for i in self.ct['geometry']]
        pts = [None] * len(geometries)
        for i in trange(len(geometries)):
            pts[i] = geometries[i].centroid
        
        # Transform pts array to execute kriging
        x_array = [i.x for i in pts]       
        y_array = [i.y for i in pts]

        #For each variable
        for variableName in tqdm(variables):
            krigVar = input("Perform kriging on " + variableName + "? (y/n)")

            while(krigVar.lower() != 'y' or krigVar.lower() != 'n'):
                krigVar = input("Please insert 'y' or 'n' without quotes.")
            
            if(krigVar.lower() == 'y'):
                #Create an empty numpy array with a space for data to be used in kriging process
                data = np.empty((len(geo_data['lats']), 3))
                
                #Transfrom data into array
                for i in trange(len(data)):
                    data[i][0] = geo_data['lats'][i]
                    data[i][1] = geo_data['lons'][i]
                    data[i][2] = geo_data['variables'][i][variableName]

                #Run kriging algorithm on sample data
                OK = OrdinaryKriging(data[:,0], data[:,1], data[:,2], variogram_model='linear', verbose=False, enable_plotting=False)

                #Krig on selected centroid points
                z, ss = OK.execute('points', y_array, x_array)
                
                for i in trange(0, len(x_array)):
                    
                    try:
                        krigged_variable_dict[ str((x_array[i], y_array[i])) ][variableName] = z[i]
                    except KeyError:
                        krigged_variable_dict[ str((x_array[i], y_array[i])) ] = {}
                        krigged_variable_dict[ str((x_array[i], y_array[i])) ][variableName] = z[i]


            elif(krigVar.lower() == 'n'):
                #TODO: Create case for choosing not to krig a variable. Create another dict with  points and values from non-krigged data, store in seperate file
                print("Not kriging " + variableName)
                for i in trange(len(geo_data['lats'])):
                    
                    try:
                        nonkrigged_variable_dict[ str(( geo_data['lons'][i], geo_data['lats'][i] ))][variableName] = geo_data['variables'][i][variableName]
                    except:
                        nonkrigged_variable_dict[ str(( geo_data['lons'][i], geo_data['lats'][i] ))] = {}
                        nonkrigged_variable_dict[ str(( geo_data['lons'][i], geo_data['lats'][i] ))][variableName] = geo_data['variables'][i][variableName]


        
       
        binnedData = self.binPoints(krigged_variable_dict)


        d = dj.GeoJSON_Creator(binnedData)
        binned_json_data = d.data_into_json('full')
        part_binned_json_data = d.data_into_json('part')

        with open(self.binned_out, 'w+') as file:
            file.write(binned_json_data)

        with open(self.binned_out_part, 'w+') as file:
            file.write(part_binned_json_data)
        
        return
        

    def createPtArray(self, points):
        ptArray = []
        for pt in points:
            #print(pt)
            newPoint = Point(round(pt[1], 5), round(pt[0], 5))
            ptArray.append(newPoint)
        
        return ptArray
    
    #Takes array of points in form [  [lat, lon, pm25], [...]    ]
    def createPointHashTable(self, points):
        hashTable = {}
        for pt in points:
            newPoint = Point(round(pt[1], 5), round(pt[0], 5))
            hashVal = self.hashFunction(newPoint.x, newPoint.y)
            hashTable[str(newPoint.x) + str(newPoint.y)] = pt[2]
        
        return hashTable
            
            
    def hashFunction(self, x, y):
        return (hash(abs(x) * abs(y)))
            
    #Points should be a 2D array [ [lat, lon, pm25], [...] ]
    def createGeoHash(self, geo):
        hashVal = hash(str(geo))
        return hashVal

    #Creates a hashtable to store the census tract names 
    #based on a hash of the actual geometry
    def createGeoHashTable(self):
        hashTable = {}
        geometries = [i for i in self.ct['geometry']]
        #print(self.ct[0])
        names = [i for i in self.ct['name']]
        for i in range(0, len(geometries)):
            hashTable[self.createGeoHash(str(geometries[i]))] = names[i]
        return hashTable

    def binPoints(self, variable_dict):
        finalData = []

        transformed_data = []
        for key in variable_dict.keys():
            new_data_array = []
            lon, lat = key[1:-1].split(", ")
            variables = variable_dict[key]
            new_data_array = [float(lat), float(lon), variables]
            transformed_data.append(new_data_array)

        geometries = [i for i in self.ct['geometry']]

        ptArray = self.createPtArray(transformed_data)
        pointHashTable = self.createPointHashTable(transformed_data)
        geometryHashTable = self.createGeoHashTable()

        tree = STRtree(ptArray)
        
        #Get all the points that intersect with a certain geometry
        
        for geometry in tqdm(geometries):
            pts = [o.wkt for o in tree.query(geometry)]
            if(len(pts) > 0):
                
                newData = [str(geometry), [],  geometryHashTable[self.createGeoHash(str(geometry))]]
                for point in pts:
                    point = shapely.wkt.loads(point)
                    lat = point.y 
                    lon = point.x
                    try:
                        pm25 = pointHashTable[(str(point.y) + str(point.x))]
                    except KeyError:
                        
                        pm25 = pointHashTable[(str(point.x) + str(point.y))]

                        
                    newPoint = [lat, lon, pm25]
                    newData[1] = newPoint
                finalData.append(newData)
        #print(finalData)
        return finalData  
        

