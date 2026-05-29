import skimage.io as skio
import numpy as np
import os
import scipy.ndimage as scnd
import glob
import matplotlib.pyplot as plt

import os
import glob
import numpy as np
import skimage.io as skio
from typing import List, Optional, Dict, Union
from dataclasses import dataclass
from enum import Enum
from sfdi_fitter import data as sd

class CameraType(Enum):
    """Типы поддерживаемых камер"""
    THORLABS = "THORLABS"
    LUCID = "LUCID"
    DAHENG = "DAHENG"


class ChannelKey(Enum):
    """Ключи для фильтрации каналов"""
    ALL = "ALL"
    WV = "WV"          # Длины волн
    BG = "BG"          # Фоновые изображения
    WHITE = "WHITE"    # Белый свет
    
class SFDIStackBuilder:
    """
    Класс для построения SFDIStack из набора изображений,
    организованных в определённой структуре папок.
    """
    
    def __init__(self, roi:[tuple] = (None, None, None, None), camera_type: Union[str, CameraType] = "DAHENG", bit_depth: int = 10):
        """
        Инициализация билдера.
        
        Args:
            camera_type: Тип камеры ("THORLABS", "LUCID", "DAHENG")
            bit_depth: Битовая глубина изображений (для THORLABS и DAHENG)
        """
        if isinstance(camera_type, str):
            camera_type = CameraType(camera_type)
        
        self.camera_type = camera_type
        self.bit_depth = bit_depth

        self.mask = (slice(roi[0], roi[1]), slice(roi[2], roi[3]))
    
    def read_image(self, path: str, bit_depth: int = 10, 
                   camera_type: Union[str, CameraType] = "DAHENG") -> np.ndarray:
        """
        Чтение одного raw-изображения и нормализация к диапазону [0, 1].
        
        Args:
            path: Путь к raw-файлу
            bit_depth: Битовая глубина изображения
            camera_type: Тип камеры
            
        Returns:
            2D numpy array типа float32, нормализованный к [0, 1]
        """
        if isinstance(camera_type, str):
            camera_type = CameraType(camera_type)
        
        depth_map = {
            CameraType.THORLABS: bit_depth,
            CameraType.LUCID: 8,
            CameraType.DAHENG: bit_depth
        }
        
        current_depth = depth_map.get(camera_type, bit_depth)
        img = skio.imread(path, as_gray=True).astype(np.float32)
        
        img = img.T
        crop_img = img[self.mask]
        return crop_img / (2 ** current_depth - 1)
    
    @staticmethod
    def get_channels_from_path(path: str, key: Union[str, ChannelKey] = "ALL") -> List[str]:
        """
        Получение списка каналов из директории с фильтрацией по ключу.
        
        Args:
            path: Путь к директории эксперимента
            key: Ключ фильтрации (ALL, WV, BG, WHITE)
            
        Returns:
            Отсортированный список названий каналов
        """
        if isinstance(key, str):
            key = ChannelKey(key)
        
        path_list = glob.glob(os.path.join(path, '*'))
        channels = []
        
        wv_channels = {'RED', 'GREEN', '810', '940'}
        bg_channels = {'BG_RED', 'BG_GREEN', 'BG_810', 'BG_940'}
        white_channels = {'WHITE'}
        
        for p in path_list:
            basename = os.path.basename(p)
            
            if key == ChannelKey.ALL:
                channels.append(basename)
            elif key == ChannelKey.WV and basename in wv_channels:
                channels.append(basename)
            elif key == ChannelKey.BG and basename in bg_channels:
                channels.append(basename)
            elif key == ChannelKey.WHITE and basename in white_channels:
                channels.append(basename)
        
        return sorted(channels)
    
    def read_single_channel(self, path: str, channel_name: str) -> Dict[str, np.ndarray]:
        """
        Чтение всех изображений из одного канала.
        
        Args:
            path: Путь к директории эксперимента
            channel_name: Название канала
            
        Returns:
            Словарь {имя_файла: изображение}
        """
        basepath = os.path.join(path, channel_name)
        file_paths = glob.glob(os.path.join(basepath, '*'))
        
        channel_data = {}
        for file_path in file_paths:
            img = self.read_image(file_path, self.bit_depth, self.camera_type)
            basename = os.path.basename(file_path)
            channel_data[basename] = img
        
        return channel_data
    
    def read_all_wavelength_channels(self, path: str, key:Union[str, ChannelKey] = "WV") -> Dict[str, Dict[str, np.ndarray]]:
        """
        Чтение всех каналов по заданному ключу
        
        Args:
            path: Путь к директории эксперимента
            key: Ключ фильтрации каналов (WV, BG, WHITE, ALL)
            
        Returns:
            Вложенный словарь {канал: {имя_файла: изображение}}
        """
        if isinstance(key, str):
            key = ChannelKey(key)
        
        channels = self.get_channels_from_path(path=path, key=key)
        
        all_data = {}
        for channel in channels:
            all_data[channel] = self.read_single_channel(path, channel_name=channel)
        
        return all_data
    
    def good_channel_name_wv(self, channel):
    
        good_names_dct = {'GREEN': '525', 'RED': '635', '810': '810', '940': '950',
                          '525': '525', '635': '635'}

        return good_names_dct[channel]
    
    
    def build_sfdi_stack(self, path: str, spat_freqs:list) -> 'SFDIStack':
        """
        Построение SFDIStack из данных эксперимента.
        
        Args:
            path: Путь к директории эксперимента
            
        Returns:
            Объект SFDIStack с данными
        """
    
        data_wv = self.read_all_wavelength_channels(path, key=ChannelKey.WV)

        if not data_wv:
            raise ValueError(f"No wavelength channels found in {path}")

        channels = sorted(data_wv.keys())

        dct_number =  {}

        for chan in channels:
            for number_key, img in data_wv[chan].items():

                number = int(number_key.split('_')[0])
                time = (number_key.split('_')[1])

                if number not in dct_number.keys():
                    dct_number[number] = []
                    dct_number[number].append(img)

                else:
                    dct_number[number].append(img)

        result_dct = {}

        for key in dct_number.keys():

            stack = np.array(dct_number[key])
            stack = stack[: , np.newaxis, :, :]

            stack = sd.SFDIStack(stack, axis_names=[sd.StackAxis.WAVELENGTH,
                                                        sd.StackAxis.FREQUENCY,
                                                         sd.StackAxis.X,
                                                         sd.StackAxis.Y],
                            spatial_frequencies=spat_freqs,
                            wavelengths = [self.good_channel_name_wv(channel) for channel in channels])

            result_dct[key] = stack

        return result_dct

def read_image(path,bit_depth=10,camera_type='THORLABS'):
    """
    read single raw image from given path
    and return float32 image normalized to 2^bit_depth - 1

    :param path: (string) path to raw file
    :param bit_depth: (int) bit_depth of grayscale image (only valid for camera_type == 'THORLABS')
    :param camera_type: (str) "THORLABS" or "LUCID" - changes the reading type for camera
    
    :return: 2d np.array - grayscale image of type np.float32
    """
    
    if camera_type == 'THORLABS':
        return skio.imread(path, as_gray=True).astype(np.float32) / (2**bit_depth - 1)
    
    if camera_type == 'LUCID':
        bit_depth = 8
        return skio.imread(path,as_gray=True).astype(np.float32)/(2**bit_depth - 1)
    

def read_single_frequency(folder,frequency_prepend='01',n_phases=6,start=0,
                          image_ext='TIF',
                          **read_image_kwargs):
    """
    read images that corresponds to the same frequency and different phase shifts
    example path to images are '24_0.TIF', '24_1.TIF', '24_2.TIF'
    (three images, that corresponds to frequency_prepend='24' and phase_shift=0, 1 and 2)

    :param folder:(str) path to folder where images for different phases are stored
    :param frequency_prepend:(str) prepend for frequency, e.g. '24' for images '24_0.TIF', '24_1.TIF', '24_2.TIF'
    :param n_phases:(int) number of phases to read
    :param start:(int) start phase number (0
    :return: 3d numpy array of shape (n_phases, Nx,Ny) where Nx,Ny are number of pixels along x and y dimensions
    """
    paths = [os.path.join(folder,f'{frequency_prepend}_{i}.{image_ext}') 
                 for i in range(start,n_phases+start)]
    
    return np.stack([read_image(path,**read_image_kwargs) for path in paths])


def calculate_Mac(phases):
    """
    Calculate alternating component of transport function (Mac)
    for given image (`phases`) using classic equation from Cuccia

    (2^0.5/3)*((I1-I2)^2 + (I1-I3)^2 + (I2-I3)^2)^0.5
    :param phases: (3d np.array) numpy array of stack
    :return:
    """
    s=0
    n=len(phases)
    for i in range(n):
        for j in range(i,n):
            s+=(phases[i]-phases[j])**2
        
    return (2 ** 0.5 / n) * s**0.5


def calculate_Mdc(phases):
    """
    Calculate direct component Mdc using the equation
    1/n*(I1+I2+I3+...In)

    :param phases (3d np.array): - numpy array stack of shape (n_phases,Nx,Ny)
    :return: (2d np.array) - numpy array stack of Mdc (Nx,Ny)
    """
    s=0
    n=len(phases)
    for i in range(n):
        s+=phases[i]
    return 1 / n * s


def read_sfdi_stack(folder, freq_prepends, n_phases=6, start_phase=0, background_substraction=False,image_ext='TIF',**read_image_kwargs):
    """
    read SFDI_stack for single experiment, i.e. read all images
    from folder for different phases and spatial frequencies and
    return frequencies list, raw_intensities stack, alternating component Mac
    and stack of direct component Mdc

    single image for one spatial frequency is read using `read_single_frequency`
    Mac and Mdc components are calculated using `calculate_Mac` and `calculate_Mdc`

    :param folder: (str) path i.e. /2tb_drive/SFDI/data/experiment_1/
    :param freq_prepends: (list of str) list of frequencies prepends for given experiment, i.e. ['01','02','04','12','24']
    :param n_phases: (int) number of phases to read in raw_intensities stack
    :param start_phase: (int) start phase increment (i.e. one can start from increment 3 and read n_phases=3 phases: '24_3.TIF','24_4.TIF','24_5.TIF')
    :read_image_kwargs are camera_type = {'THORLABS','LUCID'}
    
    :return: tuple of four objects:
    - frequencies -- 1d np.array of shape (len(freq_prepends),)
    - raw_intensities -- (4d np.array stack of shape (len(freq_prepends),n_phases,Nx,Ny)),
    - Mac stack of shape (len(freq_prepends), Nx, Ny)
    - Mdc stack of shape (len(freq_prepends), Nx, Ny)
    

    """
    macs = []
    mdcs = []
    raw_intensities = []
    
    if background_substraction:
        background_path = folder+f'/000.{image_ext}'
        bit_depth = 10
        background_img = read_image(background_path)
        
    for freq_prepend in freq_prepends:
        phases = read_single_frequency(folder, frequency_prepend=freq_prepend,
                                       n_phases=n_phases, start=start_phase,
                                       image_ext=image_ext,**read_image_kwargs)
        if background_substraction:
            phases -= background_img

        raw_intensities.append(phases)
        macs.append(calculate_Mac(phases))
        mdcs.append(calculate_Mdc(phases))

    return np.array([int(prepend) for prepend in freq_prepends]), np.stack(raw_intensities), \
           np.stack(macs), np.stack(mdcs)


def get_binned_stack(stack, kernel_size=3, pooling=True):
    """
    binarize SFDI-stack along spatial coordinates using uniform filter (mean calculation)

    :param stack: (3d np.array) SFDI-stack as 3d-array of shape (spatial_frequencies,Nx,Ny)
    :param kernel_size: (int) odd positive integer (1,3,5,...)
    :param pooling: (bool) use pooling (leave only kernel_size//2 amount of pixels) if True, else return full-sized image
    :return: (3d np.array) of stack of shape stack.shape (pooling = False)
          or (stack.shape[0],2*stack.shape[1]//kernel_size,2*stack.shape[2]//kernel_size)
    """

    if kernel_size == 1:
        return stack

    uniform_kernel = 1 / (kernel_size ** 2) * np.ones((1, kernel_size, kernel_size))
    binned_stack = scnd.convolve(stack, weights=uniform_kernel,
                                 mode='nearest')

    if pooling:
        return binned_stack[:, ::max(1,kernel_size // 2), ::max(1,kernel_size // 2)]
    return binned_stack


def get_available_frequencies(folder,image_ext='TIF'):
    """
    get list of all available frequency prepends in single folder with different images

    :param folder: (str)
    :param image_ext: (str) - extension of image
    :return: (list) list of string with available frequency prepends
    """
    filepaths = glob.glob(os.path.join(folder, f'*.{image_ext}'))
    freqs = set()

    for path in filepaths:
        splits = os.path.basename(path).split('_')

        if len(splits) == 2 and int(splits[0]) < 70:
            freqs.add(splits[0])
    return sorted(list(freqs))


def read_and_preprocess(sample_folder, binning_kernel_size=9, start_phase=0,n_phases=6, zero_freq=False,
                        background_substraction=False, verbose=True,image_ext='TIF',return_raw_intensities=False,
                        **read_image_kwargs):
    """
    Preprocess sample_folder for single SFDI experiment using following steps:
     1. read all available frequencies using `get_available_frequencies(sample_folder)`
     2. calculate raw_intensities stack, Mac stack, Mdc stack
     3. do spatial binning for Mac stack for given binning_kernel_size

    :param sample_folder: (str) path to folder with single SFDI-experiment
    :param binning_kernel_size: (int) spatial binning
    :param start_phase: start_phase for read_sfdi_stack function
    :param verbose: (bool) verbosity -- plot various images including different raw_intensity values and Mac components
    :return: tuple of two:
        -frequency_prepends (list),
        -binned_mac (Binned Mac 3d np.array stack of shape (len(frequency_prepends),Nx,Ny)
    """
    # we need to obtain available frequencies for images in folder
    frequencies = get_available_frequencies(sample_folder,image_ext=image_ext)

    # now we read and concatenate SFDI stack
    # reading only 3 phases for classic SFDI
    freqs, raw_intensities, mac_stack, mdc_stack = read_sfdi_stack(sample_folder, frequencies,
                                                                   n_phases=n_phases, start_phase=start_phase,image_ext=image_ext,**read_image_kwargs)
                                                                   

    # currently forget about Mdc (may be we should return to it later...)
    binned_mac = get_binned_stack(mac_stack, kernel_size=binning_kernel_size, pooling=True)


    if verbose:
        print(f'Processing folder\n"{sample_folder}"')
        print('Available frequencies are:')
        print(frequencies)

        print('----')

        print('Visualizing different frequencies:')

        for i, phases in enumerate(raw_intensities):

            if i % 5 == 0:
                plt.figure(figsize=(20, 5))
            plt.subplot(1, 5, i % 5 + 1)
            plt.imshow(np.swapaxes(np.swapaxes(phases, 0, 1),1,2)[:,:,:3])
            plt.title(f'frequency_prepend = {frequencies[i]}')

            if i % 5 == 4 or i == len(frequencies) - 1:
                plt.show()

        print('visualizing Mac')
        for i, mac in enumerate(mac_stack):

            if i % 5 == 0:
                plt.figure(figsize=(20, 5))
            plt.subplot(1, 5, i % 5 + 1)
            plt.imshow(mac)
            plt.title(f'frequency_prepend = {frequencies[i]}')

            if i % 5 == 4 or i == len(frequencies) - 1:
                plt.show()

        print('Non-binned Mac stack shape', mac.shape)
        print('Binned Mac stack shape', binned_mac.shape)

        print('------ END OF PREPROCESSING -------')
    
    
    if zero_freq:
        
        binned_mdc = get_binned_stack(mdc_stack, kernel_size=binning_kernel_size, pooling=True)
        mean_mdc = np.expand_dims(binned_mdc.mean(axis=0),axis=0)
        mdc_and_mac = np.append(mean_mdc,binned_mac,axis=0)
        total_freqs = np.append([0],freqs)
        if return_raw_intensities:
            return freqs, raw_intensities, mac_stack, mdc_stack
        return total_freqs, mdc_and_mac
    else:
        if return_raw_intensities:
            return freqs, raw_intensities, binned_mac
        return freqs, binned_mac


def swap_axes(stack):
    return np.swapaxes(np.swapaxes(stack,0,1),1,2)