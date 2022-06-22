import netCDF4 # needed to read and edit netCDF4 files
import shutil # needed to make a copy of the file
import glob # needed to search current directory


files = glob.glob('./*.nc')

for file in files:
    print(file)

# start with a clean file
#shutil.copyfile('thredds_conf/content/thredds/public/best.bak', 'thredds_conf/content/thredds/public/best')

dset = netCDF4.Dataset('dev.nc', 'r+')

#for var in dset.variables.keys():
#    print(var)

dset['Total_cloud_cover_entire_atmosphere'][:] = 100
dset['Total_cloud_cover_entire_atmosphere'][:][dset['Total_cloud_cover_entire_atmosphere'][:]  <= 1000] = 150
dset.close()