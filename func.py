import pylablib as pll
from tkinter import *
from PIL import ImageTk
from PIL import Image as I
from pylablib.devices import Thorlabs
import numpy as np
import matplotlib.pyplot as plt
import os
import cv2
import pandas as pd
import glob
import time
from datetime import datetime
from PIL import Image, ImageEnhance
from tqdm import trange


# import photo_pipeline


def pics():
    patterns_path = "C:/Users/madpl/Documents/sfdi/projector/red/"

    files = glob.glob(patterns_path + '*')
    data_freq_red = pd.DataFrame(columns=np.unique([i.split('\\')[-1].split('.')[0].split('_')[0] for i in files])
                                 , index=[0, 1, 2, 3, 4, 5])

    for i in files:
        with I.open(i) as im:
            enhancer = ImageEnhance.Brightness(im)

            factor = 0.4  # gives original image
            im_output = enhancer.enhance(factor)
            data_freq_red[i.split('\\')[-1].split('_')[0]][int(i.split('\\')[-1][-5])] = im_output.copy()

    patterns_path = "C:/Users/madpl/Documents/sfdi/projector/green/"

    files = glob.glob(patterns_path + '*')

    data_freq_green = pd.DataFrame(columns=np.unique([i.split('\\')[-1].split('.')[0].split('_')[0] for i in files])
                                   , index=[0, 1, 2, 3, 4, 5])

    for i in files:
        with I.open(i) as im:
            factor = 0.6  # gives original image
            im_output = enhancer.enhance(factor)
            data_freq_green[i.split('\\')[-1].split('_')[0]][int(i.split('\\')[-1][-5])] = im.copy()
    return data_freq_red, data_freq_green


data_freq_red, data_freq_green = pics()
