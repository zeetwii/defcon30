import netCDF4
import shutil

# start with a clean file
#shutil.copyfile('thredds_conf/content/thredds/public/best.bak', 'thredds_conf/content/thredds/public/best')

dset = netCDF4.Dataset('dev.nc', 'r+')
dset['Total_cloud_cover_entire_atmosphere'][:] = 100
dset['Total_cloud_cover_entire_atmosphere'][:][dset['Total_cloud_cover_entire_atmosphere'][:]  <= 1000] = 150
dset.close()