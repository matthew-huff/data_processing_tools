import json
import csv
import numpy as np
import shapely.geometry
import shapely.wkt
import shapely
import geopandas as gpd
import time
#The purpose of this class is to create a
#GeoJSON from a number 
class DataManipulator:
    def __init__(self, data):
        self.incomes = {}
        self.population = {}
        self.pollution = {}
        self.insured = {}
        self.other_attributes = {}
        self.healthcare_access = {}
        self.transportation_pctile = {} #//27 
        self.automobile_ownership = {}   # 36//
        self.parkaccess_rate = {}            #54
        self.treecanopy = {} #56
        self.white_pct = {} #82
        self.black_pct = {} #83
        self.asian_pct = {} #84
        self.latino_pct = {} #85
        self.native_pct = {} #87
        self.dataFile = "data/HPI2_MasterFile_2019-04-24.csv"
        self.getData()
        self.dataChecker()
        self.get_other_attributes(data)
        self.data = data
        self.attributes = {
            "income" : self.incomes,
            "population" : self.population,
            "pollution" : self.pollution,
            "insured" : self.insured,
            "healhcare_access" : self.healthcare_access,
            "transportation_pctile" : self.transportation_pctile,
            "treecanopy" : self.treecanopy,
            "parkaccess_rate" : self.parkaccess_rate,
            "automobile_ownership" : self.automobile_ownership,
            "white_pct" : self.white_pct,
            "black_pct" : self.black_pct,
            "latino_pct" : self.latino_pct,
            "asian_pct" : self.asian_pct,
            "native_pct" : self.native_pct,
            "others" : self.other_attributes
        }


    def getData(self):
        file = open(self.dataFile, 'r', encoding='utf-8')
        csvReader = csv.reader(file)
        csvReader.__next__()
        for row in csvReader:
            try:
                self.incomes[row[0]] = row[50] 
                self.population[row[0]] = row[1]
                self.pollution[row[0]] = row[24]
                self.insured[row[0]] = row[30]
                self.healthcare_access[row[0]] = row[21]
                self.transportation_pctile[row[0]] = row[27]
                self.automobile_ownership[row[0]] = row[36]
                self.parkaccess_rate[row[0]] = row[54]
                self.treecanopy[row[0]] = row[56]
                self.white_pct[row[0]] = row[82]
                self.black_pct[row[0]] = row[83]
                self.asian_pct[row[0]] = row[84]
                self.latino_pct[row[0]] = row[85]
                self.native_pct[row[0]] = row[87]
            except UnicodeDecodeError:
                pass
        file.close()

    def dataChecker(self):
        file = open(self.dataFile, 'r')
        csvReader = csv.reader(file)
        for row in csvReader:
            for i in range(0, len(row)):
                if(row[i] == 'income'):
                    print('income: ' + str(i))
                elif(row[i] == 'pop2010'):
                    print('population' + str(i))
                elif(row[i] == 'insured'):
                    print('insured' + str(i))
                elif(row[i] == 'healthcareaccess_pctile'):
                    print('healthcareaccess_pctile: ' + str(i))
                elif(row[i] == 'pollution'):
                    print('pollution: ' + str(i))
                elif(row[i] == 'white_pct'):
                    print("white_pct: " + str(i))
            break

        
        file.close()

        #   DATA IN FORM [  Multipolygon Geometry, [  [x, y, pm25], [...], ... ], CensusTractCode ]
    def get_other_attributes(self, data):
        for item in data:
            for key in item[1][2]:
                #Place value in:  other_attributes[census_tract][key] = value
                try:
                    self.other_attributes[item[2]][key] = item[1][2][key]
                except KeyError:
                    self.other_attributes[item[2]] = {}
                    self.other_attributes[item[2]][key] = item[1][2][key]
               
    def data_into_json(self, size):
        d = {}
        d["type"] = "FeatureCollection"
        d["features"] = []
        for i in self.data:
            #print(i)
            dictionary = {  "type" : "Feature",
                "geometry" :  self.createGeometryDict(i[0], size), 
                "properties" : self.createPropertiesDict(i[2])}
            d["features"].append(dictionary)
        return json.dumps(d)

    
    def data_into_csv(self):
        columns = ''
        rows = ''
        for i in self.data:
            properties = self.createPropertiesDict(i[2])
            full_geom = self.getGeom(i[0], 'full')
            partial_geom = self.getGeom(i[0], 'part')
            props = ''
            if(columns == ''):
                for item in properties:
                    columns += item + ','

                columns += 'full_geom,partial_geom'
            for item in properties:
                props += str(properties[item]) + ','
            props += str(full_geom).replace(',', '.') + "," + str(partial_geom).replace(',','.')
            rows += props + '\n'
            #print(properties)
        return columns + '\n' + rows


    #Create a dictionary of various properties to return to the data_into_json function
    def createPropertiesDict(self, censusTractCode):
        propDict = {}
        propDict['name'] = censusTractCode
        for key in self.attributes.keys():
            try:
                propDict[key] = self.attributes[key][censusTractCode[1:]]
            except KeyError:
                if(key == 'others'):
                    for nextKey in self.attributes['others'][censusTractCode].keys():
                        try:        
                            propDict[nextKey] = self.attributes['others'][censusTractCode][nextKey]
                        except KeyError:
                            pass
                else:
                    pass
        return propDict



    def createGeometryDict(self, geom, size):
        g = self.getGeom(geom, size)
        return g.__geo_interface__

    def getGeom(self, geom, size):
        geometry = shapely.wkt.loads(geom)
        
        buffPercentage = -0.22
        if(size == 'part'):
            minVal = min(np.max(geometry.geoms[0].exterior.xy[0]) - np.min(geometry.geoms[0].exterior.xy[0]),
            np.max(geometry.geoms[0].exterior.xy[1]) - np.min(geometry.geoms[0].exterior.xy[1]) )

            bufferVal = buffPercentage * minVal
            
            newGeom = geometry.buffer(bufferVal)
            while(newGeom.is_empty or newGeom.area < (0.25 * geometry.area)):
                
                buffPercentage *= 0.95

                bufferVal = buffPercentage * minVal
                newGeom = geometry.buffer(bufferVal)
        else:
            newGeom = geometry

        return newGeom

    #def builtPropertiesDict(self, censusTractCode):
    def seeData(self):
        print(self.attributes)

