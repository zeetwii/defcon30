import threading    # needed for threading
import time         # needed for sleep
import struct       # needed for serial
import random
from tkinter import W       # used for random
import serial   # needed for serial
import random # needed for random
import binascii # needed for hex decoding

class MicrogridController:

    def __init__(self): #TODO: add serial ports as arguments

        #self.pay1 = serial.Serial(pay1, 115200, timeout=0.1)
        #self.pay2 = serial.Serial(pay2, 115200, timeout=0.1)

        self.yaw = 0
        self.solarAngle = 45
        self.windColor = "0 255 0"
        self.turbineColor = "0 255 0"



    def updateGrid(self, data):
        """
        Updates the grid with the new values
        """
        windWarning = 0
        windAlert = 0
        solarWarning = 0
        solarAlert = 0

        if (data["cloud_coverage_actual"]-data["cloud_coverage_inject"]) >= 0.5:
            solarAlert += 10
        elif (data["cloud_coverage_actual"]-data["cloud_coverage_inject"]) >= 0.3:
            solarAlert += 1
        elif (data["cloud_coverage_actual"]-data["cloud_coverage_inject"]) >= 0.1:
            solarWarning += 1

        if data["wind_speed_actual"] >= data["wind_speed_inject"] + 50:
            windAlert += 10
        elif data["wind_speed_actual"] >= data["wind_speed_inject"] + 30:
            windAlert += 1
        elif data["wind_speed_actual"] >= data["wind_speed_inject"] + 10:
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

        print(f"windWarning: {windWarning}")
        print(f"windAlert: {windAlert}")
        print(f"solarWarning: {solarWarning}")
        print(f"solarAlert: {solarAlert}")