from PIL import Image as I
import pandas as pd
import glob
from PIL import Image, ImageEnhance
import numpy as np
from pathlib import Path


def read_patterns(colors=['red', 'green', 'blue'], factors=[0.4, 0.6, 1],
                  patterns_folder='C:/Users/madpl/Documents/sfdi/projector/'):
    ''' 
    reads patterns to a dictionary 
    '''
    patterns_dict = {}
    for color, factor in zip(colors, factors):

        files = [str(i) for i in list((Path(f'{patterns_folder}/{color}/').glob('*')))]
        patterns_dict[color] = {}

        for file in files:
            name = file.split('\\')[-1].split('.')[0]
            with I.open(file) as im:
                enhancer = ImageEnhance.Brightness(im)

                # gives original image
                im_output = enhancer.enhance(factor)
                patterns_dict[color][name] = im_output
        return patterns_dict


def read_patterns_paths(colors=['red', 'green', 'blue'], factors=[0.4, 0.6, 1],
                  patterns_folder='C:/Users/madpl/Documents/sfdi/projector/'):
    '''
    reads patterns to a dictionary
    '''
    patterns_dict = {}
    for color, factor in zip(colors, factors):

        files = [str(i) for i in list((Path(f'{patterns_folder}/{color}/').glob('*')))]
        patterns_dict[color] = {}

        for file in files:
            name = file.split('\\')[-1].split('.')[0]
            # with I.open(file) as im:
            #     enhancer = ImageEnhance.Brightness(im)

                # gives original image
                #im_output = enhancer.enhance(factor)
            patterns_dict[color][name] = (file, factor)
        return patterns_dict