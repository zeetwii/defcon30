import matplotlib.pyplot as plt

# built in python modules
import datetime
import logging
import os
import inspect

# python add-ons
import numpy as np
import pandas as pd

import pvlib
from pvlib.location import Location

pvlib.iotools.read_ecmwf_macc('CONUS_2p5km_Best.nc', latitude=float(37.844766), longitude=float(-122.297401))


