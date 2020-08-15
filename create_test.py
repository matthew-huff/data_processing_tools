from netCDF4 import Dataset
import random
from tqdm import trange
import numpy as np
filename = 'data/test.nc'

r = Dataset(filename, 'r+', format="NETCDF3_CLASSIC")

r.createVariable('jj', float, ('Time', 'south_north', 'west_east'))
for i in trange(len(r['jj'])):
    r['jj'][i] = np.random.rand(len(r['jj'][i]), len(r['jj'][i][0]))

print(r)

    

