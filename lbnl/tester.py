import glob # needed for file view
import netCDF4 # needed for weather files
import sys # needed to exit
from datetime import datetime, timedelta # needed for time calcs
import numpy as np # needed for stuff
import pandas as pd 
import pvlib # needed for pv calc
import math # needed for wind calcs

import serial # needed for serial comms
import serial.tools.list_ports # needed to list com ports
import time # needed for sleep
import struct # needed for serial messages
import random # needed for random



class MicrogridTester:

    def __init__(self, actual, injected, sol, wnd):
        """
        Init method

        Args:
            actual (str): The file path to the NetCDF4 file representing the real weather
            injected (str): The file path to the NetCDF4 file representing the injected weather
            sol (str): The COM port to use to talk to the solar grid
            wnd (str): The COM port to use to talk to the wind turbine
        """

        # Set up serial interfaces
        if sol != "None":
            self.sol = serial.Serial(sol, 9600, timeout=0.1)
        else:
            self.sol = "None"

        if wnd != "None":
            self.wnd = serial.Serial(wnd, 9600, timeout=0.1)
        else:
            self.wnd = "None"

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

        # calc the average lat lon
        self.actLat = float((float(actualLatMax) + float(actualLatMin)) / 2)
        self.actLon = float((float(actualLonMax) + float(actualLonMin)) / 2)
        self.injLat = float((float(injectLatMax) + float(injectLatMin)) / 2)
        self.injLon = float((float(injectLonMax) + float(injectLonMin)) / 2)

        # figure out the run length based on if inject or real is shorter
        runLength = 0
        if len(self.actual['time']) < len(self.inject['time']):
            runLength = len(self.actual['time']) 
        else:
            runLength = len(self.inject['time']) 

        self.startTime = datetime.utcnow() # stay in UTC
        self.endTime = self.startTime + timedelta(hours=runLength)

        print(f"Actual Lat Lon: {str(self.actLat)} {str(self.actLon)}")
        print(f"Inject Lat Lon: {str(self.injLat)} {str(self.injLon)}")
        print(f"Start Time (UTC): {str(self.startTime)}")
        print(f"End Time (UTC): {str(self.endTime)}")

        #tempData = self.get_solar_positions(float(self.actLat), float(self.actLon), self.startTime, self.endTime)
        #print(str(tempData))

    def cloud_cover_to_ghi_linear(self, cloud_cover, ghi_clear, offset=35,
                              **kwargs):
        """
        Convert cloud cover to GHI using a linear relationship.
        0% cloud cover returns ghi_clear.
        100% cloud cover returns offset*ghi_clear.
        Parameters
        ----------
        cloud_cover: numeric
            Cloud cover in %.
        ghi_clear: numeric
            GHI under clear sky conditions.
        offset: numeric, default 35
            Determines the minimum GHI.
        kwargs
            Not used.
        Returns
        -------
        ghi: numeric
            Estimated GHI.
        References
        ----------
        Larson et. al. "Day-ahead forecasting of solar power output from
        photovoltaic plants in the American Southwest" Renewable Energy
        91, 11-20 (2016).
        """

        offset = offset / 100.
        cloud_cover = cloud_cover / 100.
        ghi = (offset + (1 - offset) * (1 - cloud_cover)) * ghi_clear
        return ghi

    def cloud_cover_to_irradiance_clearsky_scaling(self, cloud_cover, method='linear', **kwargs):
        """
        Estimates irradiance from cloud cover in the following steps:
        1. Determine clear sky GHI using Ineichen model and
        climatological turbidity.
        2. Estimate cloudy sky GHI using a function of
        cloud_cover e.g.
        :py:meth:`~ForecastModel.cloud_cover_to_ghi_linear`
        3. Estimate cloudy sky DNI using the DISC model.
        4. Calculate DHI from DNI and GHI.
        Parameters
        ----------
        cloud_cover : Series
            Cloud cover in %.
        method : str, default 'linear'
            Method for converting cloud cover to GHI.
            'linear' is currently the only option.
        **kwargs
            Passed to the method that does the conversion
        Returns
        -------
        irrads : DataFrame
            Estimated GHI, DNI, and DHI.
        """
        solpos = pvlib.location.Location.get_solarposition(cloud_cover.index)
        cs = pvlib.location.Location.get_clearsky(cloud_cover.index, model='ineichen',
                                        solar_position=solpos)

        method = method.lower()
        if method == 'linear':
            ghi = self.cloud_cover_to_ghi_linear(cloud_cover, cs['ghi'],
                                                **kwargs)
        else:
            raise ValueError('invalid method argument')

        dni = pvlib.irradiance.disc(ghi, solpos['zenith'], cloud_cover.index)['dni']
        dhi = ghi - dni * np.cos(np.radians(solpos['zenith']))

        irrads = pd.DataFrame({'ghi': ghi, 'dni': dni, 'dhi': dhi}).fillna(0)
        return irrads

    def solar_radiation(self, solar_elevation_current, solar_elevation_previous, cloud_coverage):
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

    def get_solar_positions(self, lat, lon, start_time, end_time):
        """
        Calculate the solar positions for the given location from start to end time.
        :param lat (float): the latitude of the the location
        :param lon (float): the longiturde of the location
        :param start_time (str): start time in YYYY-MM-DD HH:MM:SS format (i.e. 2022-06-15 00:00:00)
        :param end_time (str): end time in YYYY-MM-DD HH:MM:SS format (i.e. 2022-06-15 00:00:00)
        :return: solar_position (DataFrame)
        """
        # Definition of Location object.
        site = pvlib.location.Location(float(lat), float(lon)) # latitude, longitude, time_zone, altitude, name
        #print(str(site))

        # Definition of a time range of simulation
        times = pd.date_range(start_time, end_time, inclusive='left', freq='H', tz="UTC")

        # Estimate Solar Position with the 'Location' object
        solpos = site.get_solarposition(times)

        return solpos

    def calculate_sol_radiation(self, time_index, sol_elevations, forecast_data, y, x):

        total = 0

        for i in range(1, len(time_index)):
            cloud_cov = forecast_data.variables['Total_cloud_cover_entire_atmosphere'][i-1, y, x]
            sol_rad = self.solar_radiation(sol_elevations[i], sol_elevations[i-1], cloud_cov/100)

            print(f"cloud cover: {str(cloud_cov)} solRad = {str(sol_rad)}")

            if sol_rad >= 0:
                total += sol_rad

        return total

    def calculate_power_output(self, dset, lat, lon, rounding=1):
        solpos = self.get_solar_positions(lat, lon, self.startTime, self.endTime)

        time_index = []
        sol_elevation = []
        for index, row in solpos.iterrows():
            time_index.append(index)
            sol_elevation.append(row['apparent_elevation'])


        print(str(sol_elevation))

        total_actual_forecast = round(self.calculate_sol_radiation(time_index, sol_elevation, dset, 0, 0), rounding)
        return total_actual_forecast

    def testFiles(self):

        testLen = 0 # default
        solarAngle = 0 # default

        if len(self.actual['time']) < len(self.inject['time']): # check which has a shorter run time
            testLen = len(self.actual['time'])
        else:
            testLen = len(self.inject['time'])

        print(f"Running {str(testLen)} tests using the provided files")
        solarJump = int(180 / int(testLen))
        #print(str(solarJump))

        actWindAngle = self.calcWindAngle(self.actual, 0, 0, testLen)
        injWindAngle = self.calcWindAngle(self.inject, 0, 0, testLen)
        #print(f"actual angles: {str(actWindAngle)}")
        #print(f"inject angles: {str(injWindAngle)}")

        actWindSpeed = self.getWindSpeed(self.actual, 0, 0, testLen)
        injWindSpeed = self.getWindSpeed(self.inject, 0, 0, testLen)
        #print(f"actual speed: {str(actWindSpeed)}")
        #print(f"inject speed: {str(injWindSpeed)}")

        actCloudCoverage = self.getCloudCoverage(self.actual, 0, 0, testLen)
        injCloudCoverage = self.getCloudCoverage(self.inject, 0, 0, testLen)
        #print(f"Actual cloud coverage: {str(actCloudCoverage)}")
        #print(f"Inject cloud coverage: {str(injCloudCoverage)}")

        actualTemperature = self.getTemperature(self.actual, 0, 0, testLen)
        injTemperature = self.getTemperature(self.inject, 0, 0, testLen)
        #print(f"Actual Temperature: {str(actualTemperature)}")
        #print(f"Inject Temperature: {str(injTemperature)}")

        # Run through all the hours
        for i in range(testLen):

            print(f"Running simulation for hour {str(i)}")

            self.payloadInterface('sol', 'srv', [solarAngle, solarAngle, solarAngle, solarAngle])


            if float(injTemperature[i]) == 69 or float(injTemperature[i]) == 342.15 or float(injTemperature[i]) == 293.706 or float(injTemperature[i]) == 0 or float(injTemperature[i]) >= 373.15: # check for easter egg states
                if float(injTemperature[i]) == 69 or float(injTemperature[i]) == 342.15 or float(injTemperature[i]) == 293.706: # disco mode
                    self.payloadInterface('wnd', 'spn', [4])
                    time.sleep(0.1)
                    for i in range(5):
                        self.payloadInterface('sol', 'egg', [1])   
                        self.payloadInterface('wnd', 'all', [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)])
                        time.sleep(1)
                elif float(injTemperature[i]) == 0:
                    self.payloadInterface('sol', 'all', [0, 0, 0])
                    self.payloadInterface('wnd', 'spn', [0])
                    time.sleep(5)
                elif float(injTemperature[i]) >= 373.15: 
                    self.payloadInterface('sol', 'all', [255, 76, 0])
                    self.payloadInterface('wnd', 'smk', [5])
                    time.sleep(5)
            '''else: #Run normal
                # Wind stuff
                if actWindSpeed[i] >= injWindSpeed[i]:
                    if round(actWindSpeed[i]) <= 80:
                        self.payloadInterface('wnd', 'spn', [round(actWindSpeed[i])])
                        self.payloadInterface('sol', 'wnd', [0, 0, 255])
                        
                    else:
                        self.payloadInterface('wnd', 'spn', [0])
                        self.payloadInterface('sol', 'wnd', [0, 0, 0])
                        self.payloadInterface('wnd', 'smk', [5])

                elif (injWindSpeed[i]) >= 80:
                    self.payloadInterface('wnd', 'spn', [0])
                    self.payloadInterface('sol', 'wnd', [0, 0, 0])
                    time.sleep(0.1)
                else:
                    self.payloadInterface('wnd', 'spn', [round(actWindSpeed[i])])

                    if abs(actWindSpeed[i] - injWindSpeed[i]) >= 60:
                        self.payloadInterface('sol', 'wnd', [255, 0, 0])
                    elif abs(actWindSpeed[i] - injWindSpeed[i]) >= 40:
                        self.payloadInterface('sol', 'wnd', [0, 255, 0])
                    else:
                        self.payloadInterface('sol', 'wnd', [0, 0, 255])

                # solar stuff
                if abs(actCloudCoverage[i] - injCloudCoverage[i]) >= 80:
                    self.payloadInterface('sol', 'wnd', [0, 0, 0])
                elif abs(actCloudCoverage[i] - injCloudCoverage[i]) >= 60:
                    self.payloadInterface('sol', 'wnd', [255, 0, 0])
                elif abs(actCloudCoverage[i] - injCloudCoverage[i]) >= 40:
                    self.payloadInterface('sol', 'wnd', [0, 255, 0])
                else:
                    self.payloadInterface('sol', 'wnd', [0, 0, 255])


                # time.sleep(5)'''
            solarAngle = solarAngle + solarJump
            #time.sleep(5)
        
        self.payloadInterface('sol', 'rst', [1])
        time.sleep(0.1)
        self.payloadInterface('sol', 'rst', [1])
        time.sleep(0.1)
        self.payloadInterface('wnd', 'rst', [1])
        time.sleep(0.1)
        self.payloadInterface('wnd', 'rst', [1])
        


    def calcWindAngle(self, dataSet, x, y, runTime):

        angleList = []

        for i in range(int(runTime)):
            
            #print(str(dataSet.variables['u-component_of_wind_height_above_ground'][i, int(x), int(y), 0]))
            uComp = (float(dataSet.variables['u-component_of_wind_height_above_ground'][i, int(x), int(y), 0]))
            vComp = (float(dataSet.variables['v-component_of_wind_height_above_ground'][i, int(x), int(y), 0]))

            angleVal = math.fmod(180.0 + ((180.0 / math.pi) * math.atan2(vComp, uComp)), 360)
            angleList.append(angleVal)

        return angleList

    def getWindSpeed(self, dataSet, x, y, runTime):

        speedList = []

        for i in range(runTime):
            speedList.append(float(dataSet.variables['Wind_speed_gust_surface'][i, int(x), int(y)]))

        return speedList

    def getCloudCoverage(self, dataSet, x, y, runTime):

        cloudCoverage = []

        for i in range(runTime):
            cloudCoverage.append(float(dataSet.variables['Total_cloud_cover_entire_atmosphere'][i, int(x), int(y)]))

        return cloudCoverage

    def getTemperature(self, dataSet, x, y, runTime):

        tempList = []

        for i in range(runTime):
            tempList.append(float(dataSet.variables['Temperature_height_above_ground'][i, int(x), int(y), 0]))
            #print(str(dataSet.variables['Temperature_height_above_ground'][i, int(x), int(y)]))

        return tempList

    def payloadInterface(self, system, cmd, payloadArray):
        '''Handles sending commands to the payload over serial and returns the response'''

        fmt = "3s" + "B"*len(payloadArray)

        #print(fmt)
        #print(cmd)
        #print(payloadArray)

        packedData = struct.pack(fmt, cmd.encode(), *payloadArray)

        #print(fmt)
        if system == 'sol': # if sending message to solar grid
            if self.sol != "None": # if grid exists
                try:
                    self.sol.reset_input_buffer()
                    self.sol.reset_output_buffer()
                    self.sol.write(packedData)
                    self.sol.flush()
                    time.sleep(0.1)

                    data = self.sol.read(32)
                    while len(data.decode()) < 1:
                        self.sol.write(packedData)
                        self.sol.flush()
                        time.sleep(0.1)
                        data = self.sol.read(32)
                        time.sleep(0.1)
                    #print(data.decode())
                except IOError:
                    print("ERROR, SOL TIMEOUT")
        elif system == 'wnd': #if sending message to wind turbine
            if self.wnd != "None": #if turbine exists
                try:
                    self.wnd.reset_input_buffer()
                    self.wnd.reset_output_buffer()
                    self.wnd.write(packedData)
                    self.wnd.flush()
                    time.sleep(0.1)

                    data = self.wnd.read(32)
                    while len(data.decode()) < 1:
                        self.wnd.write(packedData)
                        self.wnd.flush()
                        time.sleep(0.1)
                        data = self.wnd.read(32)
                        time.sleep(0.1)
                    #print(data.decode())

                    if "ERROR" in data.decode():
                        #print("test")
                        self.wnd.write(packedData)
                        self.wnd.flush()
                        time.sleep(0.1)
                        data = self.wnd.read(32)
                        time.sleep(0.1)

                except IOError:
                    print("ERROR, WND TIMEOUT")


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

            tester = MicrogridTester(str(files[int(actChoice)]), str(files[int(injChoice)]), 'COM13', 'COM21')
            tester.testFiles()
            

