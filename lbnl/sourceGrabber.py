import webbrowser # needed to use web browser
from datetime import date # needed to get today's date

# default values for start and end date are today
startDate = date.today().strftime("%Y-%m-%d")
endDate = date.today().strftime("%Y-%m-%d")

#default values for bounding box are LBNL
north = 37.8933
west = -122.2974
east = -122.2181
south = 37.8447


ready = False
print("Welcome to the simple netCDF grabber for HRRR data")

while not ready:
    print("\nThe current settings are:")
    print(f"Start Date: {str(startDate)}")
    print(f"End Date: {str(endDate)}")
    print(f"Boudning box North: {str(north)}")
    print(f"Boudning box West: {str(west)}")
    print(f"Boudning box East: {str(east)}")
    print(f"Boudning box South: {str(south)}\n")

    print("Type 'D' to change dates, 'B' to change the bounding box, or anything else to continue")
    choice = input("Enter your choice: ")

    if str(choice).lower() == 'd':
        startDate = input("Enter new start date in the format of YY-MM-DD: ")
        endDate = input("Enter new end date in the format of YY-MM-DD: ")
    elif str(choice).lower() == 'b':
        north = input("Enter the new north point of the bounding box:")
        west = input("Enter the new west point of the bounding box:")
        east = input("Enter the new east point of the bounding box:")
        south = input("Enter the new south point of the bounding box:")
    else:
        ready = True

# then make a url variable
url = f"https://thredds-jumbo.unidata.ucar.edu/thredds/ncss/grib/NCEP/HRRR/CONUS_2p5km/Best?var=High_cloud_cover_high_cloud&var=Low_cloud_cover_low_cloud&var=Medium_cloud_cover_middle_cloud&var=Pressure_surface&var=Total_cloud_cover_entire_atmosphere&var=Wind_speed_gust_surface&var=Temperature_height_above_ground&var=u-component_of_wind_height_above_ground&var=v-component_of_wind_height_above_ground&north={str(north)}&west={str(west)}&east={str(east)}&south={str(south)}&horizStride=1&time_start={str(startDate)}T01%3A00%3A00Z&time_end={str(endDate)}T12%3A00%3A00Z&timeStride=1&vertCoord=&accept=netcdf"
  
# then call the default open method described above
webbrowser.open(url)