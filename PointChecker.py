import shapefile
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point, box, shape
from shapely.strtree import STRtree
import numpy as np
import matplotlib.pyplot as plt
import shapely.wkt
import time
from tqdm import tqdm, trange
import sys 
import DataIntoJSON as dj


class PointChecker:
    def __init__(self):
        """
        if(Base == 'County'):
            self.shape = shapefile.Reader("data/County_Boundary-shp/County_Boundary.shp")
            
        elif(Base == 'City'):
            self.shape = shapefile.Reader("data/City_Boundary-shp/LA_CITY3.shp")
            #print(shapefile.Reader("data/City_Boundary-shp/LA_CITY.shp"))
        """
        self.shape=shapefile.Reader('data/LA_County_City_Boundaries.shp')
        self.LAT_MIN = self.shape.bbox[1]
        self.LAT_MAX = self.shape.bbox[3]
        self.LON_MIN = self.shape.bbox[0]
        self.LON_MAX = self.shape.bbox[2]
        self.BoundingBox = box(self.LAT_MIN, self.LON_MIN, self.LAT_MAX, self.LON_MAX)
        self.poly = Polygon(self.shape.shapes().__geo_interface__['geometries'][0]['coordinates'][0])
        #print(self.shape.shapes().__geo_interface__['geometries'][0]['coordinates'][0])
        self.ct = gpd.read_file("data/census_tracts.geojson")
        self.tc = self.get_tract_centroids()

    def get_tract_centroids(self):
        geometries = [i for i in self.ct['geometry']]
        pts = [None] * len(geometries)
        for i in trange(len(geometries)):
            pts[i] = geometries[i].centroid
        return pts

    def checkPoint(self, x, y):
        point = Point(x, y)
        if(self.BoundingBox.contains(point)):  
            return True
        else:
            return False
        
    def getBBox(self):
        return self.shape.bbox

    def checkPoint2(self, y, x):
        point = Point(x, y)
        if(self.poly.contains(point)):     
            return True
        else:
            return False

    def dispCTData(self):
        print(self.ct.head())
        self.ct.plot()
        print(self.ct['geometry'][0])

        data = {}
        for ct in self.ct.iloc(0):
            name = ct['name']
        
    def hashFunction(self, x, y):
        return (hash(abs(x) * abs(y)))


    def createPtArray(self, points):
        ptArray = []
        for pt in points:
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

    def binPoints(self, points):
        finalData = []
        #print(points[0])
        #print(self.ct.iloc(0)[0])
        #self.createGeoHash(self.ct['geometry'][0])

        geometries = [i for i in self.ct['geometry']]

        ptArray = self.createPtArray(points)
        pointHashTable = self.createPointHashTable(points)
        geometryHashTable = self.createGeoHashTable()

        tree = STRtree(ptArray)
        
        #Get all the points that intersect with a certain geometry
        
        for geometry in geometries:
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
                    newData[1].append(newPoint)
                finalData.append(newData)
        #print(finalData)
        return finalData
        

#d = [['MULTIPOLYGON (((-118.303334 34.273536, -118.303178 34.273956, -118.302164 34.274158, -118.300959 34.275032, -118.299696 34.275262, -118.299357 34.276027, -118.299749 34.276706, -118.297835 34.277791, -118.297323 34.278237, -118.29697 34.278807, -118.289899 34.278946, -118.290225 34.271, -118.285616 34.270541, -118.285271 34.266434, -118.281666 34.266011, -118.278953 34.266541, -118.279483 34.26363, -118.277285 34.26363, -118.277285 34.261956, -118.278516 34.261475, -118.277404 34.261606, -118.277422 34.259903, -118.278125 34.257602, -118.278167 34.255768, -118.28498 34.255889, -118.284913 34.262463, -118.286486 34.262797, -118.294192 34.262886, -118.294338 34.2632, -118.297919 34.263222, -118.297915 34.267227, -118.297304 34.267821, -118.297928 34.268665, -118.299302 34.269288, -118.301138 34.270806, -118.301684 34.271614, -118.302753 34.272001, -118.302731 34.272495, -118.302198 34.272817, -118.302867 34.273112, -118.303334 34.273536)))', [[34.26521, -118.29464, 4.234741033718556], [34.26521, -118.28464, 3.798137423053142], [34.27521, -118.29464, 3.979233263395618], [34.27521, -118.28464, 3.4217986559288835]], '06037101122'], ['MULTIPOLYGON (((-118.299451 34.255978, -118.285924 34.255895, -118.285924 34.248018, -118.287509 34.248149, -118.289826 34.24916, -118.291215 34.250225, -118.292876 34.251138, -118.297202 34.25398, -118.299451 34.255978)))', [[34.25521, -118.29464, 4.549637718048026]], '06037101210'], ['MULTIPOLYGON (((-118.285924 34.248959, -118.285924 34.255895, -118.280992 34.255916, -118.280996 34.255803, -118.278167 34.255768, -118.278224 34.253291, -118.276916 34.253084, -118.276915 34.251582, -118.278224 34.251657, -118.278022 34.249612, -118.277611 34.249589, -118.276035 34.246636, -118.276103 34.246484, -118.27975 34.247663, -118.285924 34.248018, -118.285924 34.248959)))', [[34.25521, -118.28464, 4.32122106698925]], '06037101220']]

#a = PointChecker()
#d = a.get_tract_centroids()
#a = dj.GeoJSON_Creator(d)
#a.dataChecker()
#g = a.dataIntoJson()
#print(g)
    
