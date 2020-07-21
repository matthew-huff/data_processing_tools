import json
import csv
import numpy as np
import shapely.geometry
import shapely.wkt
import shapely
import geopandas as gpd
#The purpose of this class is to create a
#GeoJSON from a number 
class GeoJSON_Creator:
    def __init__(self, data):
        self.incomes = {}
        self.population = {}
        self.pollution = {}
        self.insured = {}
        self.other_attributes = {}
        self.healthcare_access = {}
        self.dataFile = "data/HPI2_MasterFile_2019-04-24.csv"
        self.getData()
        self.get_other_attributes(data)
        self.data = data
        self.attributes = {
            "income" : self.incomes,
            "population" : self.population,
            "pollution" : self.pollution,
            "insured" : self.insured,
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
            break

        
        file.close()

        #   DATA IN FORM [  Multipolygon Geometry, [  [x, y, pm25], [...], ... ], CensusTractCode ]
    def get_other_attributes(self, data):
        
       
        for item in data:
            #print(item)
            for key in item[1][2]:
                #Place value in:  other_attributes[census_tract][key] = value
                try:
                    

                    self.other_attributes[item[2]][key] = item[1][2][key]
                    #print(self.other_attributes)
                    #exit()
                except KeyError:
                    self.other_attributes[item[2]] = {}
                    self.other_attributes[item[2]][key] = item[1][2][key]
                    #print(self.other_attributes)
                    #exit()
               
    def ddata_into_json(self):
        d = {}
        d["type"] = "FeatureCollection"
        d["features"] = []
        for i in self.data:
            #print(i)
            dictionary = {  "type" : "Feature",
                "geometry" :  self.createGeometryDict(i[0]), 
                "properties" : self.createPropertiesDict(i[2])}
            d["features"].append(dictionary)
        return json.dumps(d)

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

    def createGeometryDict(self, geom):
        geometry = shapely.wkt.loads(geom)
        return geometry.__geo_interface__

    #def builtPropertiesDict(self, censusTractCode):
    def seeData(self):
        print(self.attributes)

