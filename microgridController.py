import threading    # needed for threading
import time         # needed for sleep
import struct       # needed for serial
import random       # used for random
import serial       # needed for serial
import random       # needed for random
import binascii     # needed for hex decoding
import math         # needed for floor

class MicrogridController:

    def __init__(self, wind): 
        """
        solar: the solar panel serial port
        wind: the wind turbine serial port
        """

        #self.solar = serial.Serial(solar, 115200, timeout=0.1)
        self.wind = serial.Serial(wind, 115200, timeout=0.1)

        self.yaw = 0
        self.easterEgg = False

    def stepPayload(self, direction, rotationAngle):
        """
        Rotates the payload in the direction of the wind
        """

        stepAngle = 0.36 #1.8 * 14 / 70

        totalSteps = int(rotationAngle / stepAngle)

        #print(f"totalSteps: {totalSteps}")

        payload = []
        payload.append(str(direction))
        payload.append(str(0))
        payload.append(str(0))

        for i in range(math.floor(totalSteps / 255)):
            payload.append(str(255))

        payload.append(str(totalSteps % 255))

        #print(f"payload: {payload}")

        return payload


    def updateGrid(self, data):
        """
        Updates the grid with the new values
        """
        windWarning = 0
        windAlert = 0
        solarWarning = 0
        solarAlert = 0

        if (data["cloud_coverage_actual"]-data["cloud_coverage_inject"]) >= 0.7:
            solarAlert += 10
        elif (data["cloud_coverage_actual"]-data["cloud_coverage_inject"]) >= 0.5:
            solarAlert += 1
        elif (data["cloud_coverage_actual"]-data["cloud_coverage_inject"]) >= 0.3:
            solarWarning += 1

        if data["wind_speed_actual"] >= data["wind_speed_inject"] + 50:
            windAlert += 10
        elif data["wind_speed_actual"] >= data["wind_speed_inject"] + 30:
            windAlert += 1
        elif data["wind_speed_actual"] >= data["wind_speed_inject"] + 10:
            windWarning += 1

        if (data["wind_direction_actual"]-data["wind_direction_inject"]) >= 90 or (data["wind_direction_actual"]-data["wind_direction_inject"]) <= -90:
            windAlert += 10
        elif (data["wind_direction_actual"]-data["wind_direction_inject"]) >= 60 or (data["wind_direction_actual"]-data["wind_direction_inject"]) <= -60:
            windAlert += 1
        elif (data["wind_direction_actual"]-data["wind_direction_inject"]) >= 30 or (data["wind_direction_actual"]-data["wind_direction_inject"]) <= -30:
            windWarning += 1

        if (abs(data["temp_low_inject"]) - abs(data["temp_low_actual"])) >= 50:
            solarAlert += 1
            windAlert += 1
        elif (abs(data["temp_low_inject"]) - abs(data["temp_low_actual"])) >= 30:
            solarWarning += 2
            windWarning += 2
        elif (abs(data["temp_low_inject"]) - abs(data["temp_low_actual"])) >= 10:
            solarWarning += 1
            windWarning += 1

        if (abs(data["temp_high_actual"]) - abs(data["temp_high_inject"])) >= 50:
            solarAlert += 1
            windAlert += 1
        elif (abs(data["temp_high_actual"]) - abs(data["temp_high_inject"])) >= 30:
            solarWarning += 2
            windWarning += 2
        elif (abs(data["temp_high_actual"]) - abs(data["temp_high_inject"])) >= 10:
            solarWarning += 1
            windWarning += 1

        if ((data["temp_low_inject"] == 69)) and (data["temp_high_inject"] == 69):
            self.easterEgg = True 

        print(f"windWarning: {windWarning}")
        print(f"windAlert: {windAlert}")
        print(f"solarWarning: {solarWarning}")
        print(f"solarAlert: {solarAlert}")
        print(f"easterEgg: {self.easterEgg}")

        if self.easterEgg:
            self.easterEgg = False
            self.payloadInterface("solar", "hse", ["0", str(random.randint(0, 255)), str(random.randint(0, 255)), str(random.randint(0, 255))])
            #TODO: Finish
        else:
            # Wind warnings
            if windAlert >= 2:
                self.payloadInterface("wind", "smk", [str(10)])
            elif windWarning >= 2 or windAlert >= 1:
                self.payloadInterface("wind", "all", [str(255), str(0), str(0)])
            elif windWarning >= 1:
                self.payloadInterface("wind", "all", [str(255), str(255), str(0)])
            else:
                self.payloadInterface("wind", "all", [str(0), str(255), str(0)])
            
            # Wind direction
            if self.yaw > data["wind_direction_inject"]: # counterclockwise
                rotationAngle = self.yaw - data["wind_direction_inject"]
                direction = 1
            else: # clockwise
                rotationAngle = data["wind_direction_inject"] - self.yaw
                direction = 0
            payload = self.stepPayload(direction, rotationAngle)
            self.payloadInterface("wind", "yaw", payload)
            

    def payloadInterface(self, type, cmd, payloadArray):
        '''Handels sending commands to the payload over serial and returns the response'''

        fmt = "3s" + "B"*len(payloadArray)
        packedData = struct.pack(fmt, cmd.encode(), *payloadArray)

        #print(fmt)
        try:
            if type == "wind":
                self.wind.write(packedData)
                self.wind.flush()

                time.sleep(0.1)

                data = self.wind.read(32)

                while len(data.decode()) < 1:
                    self.wind.write(packedData)
                    self.wind.flush()
                    time.sleep(0.1)
                    
                    data = self.wind.read(32)
                    time.sleep(0.1)
                return data.decode()
            elif type == "solar":
                self.solar.write(packedData)
                self.solar.flush()

                time.sleep(0.1)

                data = self.solar.read(32)

                while len(data.decode()) < 1:
                    self.solar.write(packedData)
                    self.solar.flush()
                    time.sleep(0.1)
                    
                    data = self.solar.read(32)
                    time.sleep(0.1)
                return data.decode()
        except IOError:
            return "ERROR TIMEOUT"