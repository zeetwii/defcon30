import netCDF4 # needed to read and edit netCDF4 files
import shutil # needed to make a copy of the file
import glob # needed to search current directory
import sys # needed to exit


files = glob.glob('./*.nc')

if len(files) < 1:
    print("No netCDF4 files found in current directory")
    print("Please make sure that all netCDF files are using '.nc' as a file extension")
    sys.exit(1)
else:
    print("List of '.nc' files:")
    for i in range(len(files)):
        print(f'File {str(i)} : {str(files[i])}')

fileChoice = input('Enter the number of the file to use, or anything to exit:')

if str(fileChoice).isdigit():
    print(f'Using {str(files[int(fileChoice)])}')
else:
    print('Not an int, exiting')
    sys.exit()

# start with a clean file
#shutil.copyfile('thredds_conf/content/thredds/public/best.bak', 'thredds_conf/content/thredds/public/best')

dset = netCDF4.Dataset('dev.nc', 'r+')

#for var in dset.variables.keys():
#    print(var)

dset['Total_cloud_cover_entire_atmosphere'][:] = 100
dset['Total_cloud_cover_entire_atmosphere'][:][dset['Total_cloud_cover_entire_atmosphere'][:]  <= 1000] = 150
dset.close()