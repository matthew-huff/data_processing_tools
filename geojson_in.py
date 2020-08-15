#This set of functions is meant to take in a .geojson file and create a pandas dataframe from it

import pandas as  pd 
import csv
import json
import argparse
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from numpy import cov
from scipy.stats import pearsonr
from scipy.stats import spearmanr
import pingouin as pg
import seaborn as sns
from netCDF4 import Dataset
def geojson_to_pandas(geojson_filename):
    #Open file and read in the json
    file = open(geojson_filename, 'r')
    geojson_reader = json.load(file)
    
    #Initialize a dictionary for variables in the form { var1 : [...],  var2 : [...] }
    varDict = {}
    for i in geojson_reader['features'][0]['properties']:
        varDict[i] = []

    
    for i in geojson_reader['features']:
        #Skip any rows with incomplete data
        if(len(i['properties']) < len(geojson_reader['features'][0]['properties'])):
            pass

        #Place data into dict/array
        else:
            for var in i['properties']: 
                
                try:
                    value = float(i['properties'][var])
                    varDict[var].append(value)
                
                except:
                    varDict[var].append(0)

 
    #Create a pandas dataframe
    df = pd.DataFrame(varDict)
    preprocess_pandas(df)
    return df
    #print(variables)

def check_nc_file():
    file = Dataset('data/wrfout_d03_2012_fake.nc', 'r', format="NETCDF4")
    print(file['PM25'][0][100][100])



def preprocess_pandas(df):
    scaler = MinMaxScaler()
    df[["income", "insured", "pm25"]] = scaler.fit_transform((df[["income", "insured", "pm25"]]))
    covariance = cov(df['income'], df['pm25'])
    pear_cov, _ = pearsonr(df['income'], df['pm25'])
    spearmans_cov = spearmanr(df['income'], df['pm25'])
    print(pg.corr(x=df['income'], y=-df['pm25']))
    #print("Covariance: " + str(covariance))
    #print("Pearsons: " + str(pear_cov))
    #print("Spearmans: " + str(spearmans_cov))
    

def plot_cor(df):

    f, ax = plt.subplots(figsize=(10, 6))
    corr = df.corr()
    hm = sns.heatmap(round(corr,2), annot=True, ax=ax, cmap="coolwarm",fmt='.2f',
                    linewidths=.05)
    f.subplots_adjust(top=0.93)
    t = f.suptitle('PM25 correlation heatmap', fontsize=14)


def main():

    arg = argparse.ArgumentParser()

    arg.add_argument('-f', '--file', help="input .geojson filename.  geojson should be averaged data.")
    args = arg.parse_args()
    args = vars(args)
   

    df = geojson_to_pandas(args['file'])

    plot_cor(df)

check_nc_file()
    


