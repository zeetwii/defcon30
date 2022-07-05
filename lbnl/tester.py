import glob # needed for file view
import netCDF4 # needed for weather files
import sys # needed to exit
import pandas as pd
from pvlib.location import Location
import math


class MicrogridTester:

    def __init__(self, actual, injected):
        """
        Init method

        Args:
            actual (str): The file path to the NetCDF4 file representing the real weather
            injected (str): The file path to the NetCDF4 file representing the injected weather
        """

        self.actual = netCDF4.Dataset(actual, 'r+')
        self.inject = netCDF4.Dataset(injected, 'r+')

        # pull lat lon values from actual file
        actualLatMin = self.actual.geospatial_lat_min
        actualLonMin = self.actual.geospatial_lon_min
        actualLatMax = self.actual.geospatial_lat_max
        actualLonMax = self.actual.geospatial_lon_max

        # pull lat lon values from inject file
        injectLatMin = self.inject.geospatial_lat_min
        injectLonMin = self.inject.geospatial_lon_min
        injectLatMax = self.inject.geospatial_lat_max
        injectLonMax = self.inject.geospatial_lon_max

        self.actLat = float((float(actualLatMax) + float(actualLatMin)) / 2)
        self.actLon = float((float(actualLonMax) + float(actualLonMin)) / 2)
        self.injLat = float((float(injectLatMax) + float(injectLatMin)) / 2)
        self.injLon = float((float(injectLonMax) + float(injectLonMin)) / 2)

        print(f"Actual Lat Lon: {str(self.actLat)} {str(self.actLon)}")
        print(f"Inject Lat Lon: {str(self.injLat)} {str(self.injLon)}")

    def solar_radiation(solar_elevation_current, solar_elevation_previous, cloud_coverage):
        """
        Calculate the solar radiation based upon the suns elevation angle currently and previously 
        along with the total cloud coverage

        Args:
            solar_elevation_current (float): current solar elevation in degrees
            solar_elevation_previous (float): previous solar elevation in degrees
            cloud_coverage (float): percentage of cloud coverage from 0.0 - 1.0

        Returns:
            float: the solar radiation for the given location
        """
        avg_angle = (solar_elevation_previous + solar_elevation_current)/2
        r_o = 990 * math.sin(math.radians(avg_angle - 30))

        return (r_o * (1 - (.75 * (cloud_coverage ** 3.4))))

    def testFiles(self):

        testLen = 0 # default

        if len(self.actual['time']) < len(self.inject['time']): # check which has a shorter run time
            testLen = len(self.actual['time'])
        else:
            testLen = len(self.inject['time'])

        print(f"Running {str(testLen)} tests using the provided files")


if __name__ == "__main__":
    files = glob.glob('./*.nc')

    if len(files) < 1:
        print("No netCDF4 files found in current directory")
        print("Please make sure that all netCDF files are using '.nc' as a file extension")
        sys.exit(1)
    else:
        print("List of '.nc' files:")
        for i in range(len(files)):

            temp = str(files[i]).split('\\')
            files[i] = temp[len(temp) - 1]

            print(f'File {str(i)} : {str(files[i])}')

    actChoice = input('Enter the number of the file to use for actual data, or anything to exit: ')
    injChoice = input('Enter the number of the file to use for inject data, or anything to exit: ')


    if str(actChoice).isdigit() and str(injChoice).isdigit():
        if int(actChoice) < len(files) and int(injChoice) < len(files):
            print(f'Using {str(files[int(actChoice)])} for actual data')
            print(f'Using {str(files[int(injChoice)])} for inject data')

            tester = MicrogridTester(str(files[int(actChoice)]), str(files[int(injChoice)]))
            tester.testFiles()

