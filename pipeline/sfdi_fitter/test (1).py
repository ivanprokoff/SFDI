from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import numpy as np
from enum import Enum
import os

import cv2
import itertools as iterto
from cv2 import aruco
import sfdi_fitter
import sfdi_fitter.data as sd
from sfdi_fitter.pipeline import SFDIPipeline
from sfdi_fitter import preprocess
import sfdi_fitter.demodulation as dmd
import sfdi_fitter.reflectance as sr
import sfdi_fitter.transformers as tr
import sfdi_fitter.preprocess as pr
import matplotlib.pyplot as plt


@dataclass
class SFDIStackMeasurement:
    """
    Обертка для SFDIStack с добавлением мета-информации.
    
    Attributes:
        stack (SFDIStack): Основной SFDI стек данных
        white (Optional[np.array]): white photo
        aruco_coords (Optional[list]): Список координат Aruco маркеров
        ## time (Optional[time]): Время съемки каждой длины волны
        ## acquisition_params (Optional[Dict[str, Any]]): Параметры acquisition
        ## roi_info (Optional[Dict[str, Any]]): Информация об области интереса
        custom_metadata (Optional[Dict[str, Any]]): Пользовательские метаданные
    """
    
    ARUCO_BEST_PARAMS: dict = field(default_factory=lambda: {
    'athr_min': 5,
    'athr_max': 31,
    'athr_step': 8,
    'athr_const': 10.419057258363551,
    'min_perim': 0.017534774392741755,
    'poly_acc': 0.02410959219921611,
    'min_corner_dist': 0.07727238443203809,
    'min_otsu': 1.330148826015381,
    'persp_margin': 0.13835293052040726,
    'max_err_border': 0.4566747929422762,
    'err_correction': 0.8952068376871993,
    'clahe_clip': 2.5583872105783305,
    'blur_ksize': 7,
    'morph_op': 'close',
    'morph_ksize': 5,
    }, repr=False, init=False)
    
    stack: sd.SFDIStack
    white_img: Optional[np.array] = None
    glucose_mmol: Optional[float] = None
    aruco_coords: Optional[dict] = None
    aruco_coords_mod: Optional[dict] = None
    temperature: Optional[list] = None
    date: Optional[str] = None
    time: Optional[str] = None
    roi_mask_corr: Optional[list] = None
    
    def __repr__(self) -> str:
        """Строковое представление обертки"""
        
        repr_string = f"""SFDIStackMeasurement(stack={repr(self.stack)}"""

        if self.white_img is not None:
            repr_string += f",\n white_img=np.ndarray(shape={self.white_img.shape}, dtype={self.white_img.dtype})"
        if self.aruco_coords is not None:
            repr_string += f",\n aruco_coords={self.aruco_coords}"
        if self.aruco_coords_mod is not None:
            repr_string += f",\n aruco_coords_mod={self.aruco_coords_mod}"
            
#         if self.measurement_time is not None:
#             repr_string += f",\n measurement_time={repr(self.measurement_time.strftime('%Y-%m-%d %H:%M:%S'))}"

        if self.temperature is not None:
            repr_string += f",\n temperature={self.temperature}"
        if self.date is not None:
            repr_string += f",\n date: {self.date}, time: {self.time}"
        if self.glucose_mmol is not None:
            repr_string += f', \n glucose:{self.glucose_mmol}'
        if self.roi_mask_corr is not None:
            repr_string += f', \n roi_mask_corr:{self.roi_mask_corr}'
#         if self.roi_info is not None:
#             repr_string += f",\n roi_info={self.roi_info}"
#         if self.custom_metadata is not None:
#             repr_string += f",\n custom_metadata={self.custom_metadata}"

        repr_string += ")"
        return repr_string
    
    # Делегирование методов исходного класса
    @property
    def data(self) -> np.ndarray:
        """Делегирование свойства data"""
        return self.stack.data
    
    @property
    def shape(self) -> tuple:
        """Делегирование свойства shape"""
        return self.stack.shape
    
    @property
    def dtype(self):
        """Делегирование свойства dtype"""
        return self.stack.dtype
    
    @property
    def axis_names(self) -> List:
        """Делегирование свойства axis_names"""
        return self.stack.axis_names
    
    def get_axis_index(self, axis_name):
        """Делегирование метода get_axis_index"""
        return self.stack.get_axis_index(axis_name)
    
    def reorder_axes(self, new_axis_order, inplace=True):
        """Делегирование метода reorder_axes"""
        result = self.stack.reorder_axes(new_axis_order, inplace)
        if inplace:
            return self
        return SFDIStackWithMeta(
            stack=result,
            image_id=self.image_id,
            timestamp=self.timestamp,
            patient_info=self.patient_info,
            acquisition_params=self.acquisition_params,
            roi_info=self.roi_info,
            notes=self.notes,
            tags=self.tags,
            custom_metadata=self.custom_metadata
        )
    
    def get_noncoord_axes(self):
        """Делегирование метода get_noncoord_axes"""
        return self.stack.get_noncoord_axes()
    
    def iterate_over_axes(self, *axis_names):
        """Делегирование метода iterate_over_axes"""
        yield from self.stack.iterate_over_axes(*axis_names)
    
    def get_standard_axis_order(self):
        """Делегирование метода get_standard_axis_order"""
        return self.stack.get_standard_axis_order()
    
    def squeeze(self, axis_name=None, inplace=True):
        """Делегирование метода squeeze"""
        result = self.stack.squeeze(axis_name, inplace)
        if inplace:
            return self
        return SFDIStackWithMeta(
            stack=result,
            image_id=self.image_id,
            timestamp=self.timestamp,
            patient_info=self.patient_info,
            acquisition_params=self.acquisition_params,
            roi_info=self.roi_info,
            notes=self.notes,
            tags=self.tags,
            custom_metadata=self.custom_metadata
        )
    
    # Дополнительные методы для работы с мета-информацией
    
    
    def find_aruco_markers(self, polygon_accuracy_rate=0.01, verbose=False):
        '''
        Ищет Aruco маркеры на white
        Params
        -----------------
            polygon_accuracy_rate - параметр, влияющий на эффективность детектирования маркеров
        -----------------
        Return
        -----------------
            center_lst - список [y,x] координат маркеров, отсортированный по ids - порядковый номер маркеров при генерации
            (порядок соответствует обходу по часовой стрелке, начиная с верхнего левого края)
        '''
          
        detectorParams = cv2.aruco.DetectorParameters()
        detectorParams.polygonalApproxAccuracyRate = polygon_accuracy_rate
        
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        detector = cv2.aruco.ArucoDetector(dictionary, detectorParams)

        img = self.white_img

        if img.dtype != np.uint8:
            gray_img = np.stack([(img.T/img.max() * 255).astype(np.uint8)]*3,axis=-1)
        else:
            gray_img = img
        corners, ids, rejected = detector.detectMarkers(gray_img[:, :, 0])
        center_lst = self.get_central_aruco_markers(corners)
        
        if verbose:
            for _corners in corners:
                pts = _corners.reshape((-1, 1, 2)).astype(np.int32)
                cv2.polylines(gray_img, [pts], True, (0, 255, 0), thickness=5)
                
            plt.imshow(gray_img)

            for y, x in center_lst:
                plt.scatter(x, y, color='red')
        
        aruco_coords_dct = dict(zip(list(ids[:, 0]), center_lst))

        if 2 not in aruco_coords_dct.keys():
            aruco_coords_dct[2] = [np.nan, np.nan]
        if 3 not in aruco_coords_dct.keys():
            aruco_coords_dct[3] = [np.nan, np.nan]
            
        self.aruco_coords = aruco_coords_dct
        return ids, center_lst
    
    
    def find_aruco_markers_v2(self, params=None, verbose=False):
        """Улучшенная детекция ArUco маркеров."""
        BEST = {
            'athr_min': 5,
            'athr_max': 31,
            'athr_step': 8,
            'athr_const': 10.419057258363551,
            'min_perim': 0.017534774392741755,
            'poly_acc': 0.02410959219921611,
            'min_corner_dist': 0.07727238443203809,
            'min_otsu': 1.330148826015381,
            'persp_margin': 0.13835293052040726,
            'max_err_border': 0.4566747929422762,
            'err_correction': 0.8952068376871993,
            'clahe_clip': 2.5583872105783305,
            'blur_ksize': 7,
            'morph_op': 'close',
            'morph_ksize': 5,
        }
        if params is not None:
            BEST.update(params)

        img = self.white_img

        gray = (img.T / img.max() * 255).astype(np.uint8)

        if BEST['clahe_clip'] > 0:
            clahe = cv2.createCLAHE(BEST['clahe_clip'], (8, 8))
            gray = clahe.apply(gray)

        k = int(BEST['blur_ksize'])
        if k >= 3:
            if k % 2 == 0:
                k += 1
            gray = cv2.GaussianBlur(gray, (k, k), 0)

        if BEST['morph_op'] != 'none':
            mk = int(BEST['morph_ksize'])
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (mk, mk))
            if BEST['morph_op'] == 'open':
                gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
            elif BEST['morph_op'] == 'close':
                gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            elif BEST['morph_op'] == 'dilate':
                gray = cv2.dilate(gray, kernel)
            elif BEST['morph_op'] == 'erode':
                gray = cv2.erode(gray, kernel)

        p = cv2.aruco.DetectorParameters()
        p.adaptiveThreshWinSizeMin = int(BEST['athr_min'])
        p.adaptiveThreshWinSizeMax = int(BEST['athr_max'])
        p.adaptiveThreshWinSizeStep = int(BEST['athr_step'])
        p.adaptiveThreshConstant = float(BEST['athr_const'])
        p.minMarkerPerimeterRate = float(BEST['min_perim'])
        p.polygonalApproxAccuracyRate = float(BEST['poly_acc'])
        p.minCornerDistanceRate = float(BEST['min_corner_dist'])
        p.minOtsuStdDev = float(BEST['min_otsu'])
        p.perspectiveRemoveIgnoredMarginPerCell = float(BEST['persp_margin'])
        p.maxErroneousBitsInBorderRate = float(BEST['max_err_border'])
        p.errorCorrectionRate = float(BEST['err_correction'])

        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        detector = cv2.aruco.ArucoDetector(dictionary, p)
        corners, ids, _ = detector.detectMarkers(gray)

        center_lst = self.get_central_aruco_markers(corners) if corners else []

        if ids is not None and len(ids) > 0:
            aruco_coords_dct = dict(zip(ids.flatten().tolist(), center_lst))
        else:
            aruco_coords_dct = {}

        for expected_id in [2, 3]:
            if expected_id not in aruco_coords_dct:
                aruco_coords_dct[expected_id] = [np.nan, np.nan]

        self.aruco_coords = aruco_coords_dct
        return ids, center_lst

    def plot_aruco_coords(self):
        
        c_dct = {2:'o', 3:'s'}
        for id_, (x, y) in self.aruco_coords.items():
            
            plt.scatter(x, y, c='r', label=id_, marker=c_dct[id_], s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
        plt.legend()

    def get_central_aruco_markers(self, bboxs):
        '''
        Функция получает на вход массив отсортированных Aruco координат угловых позиций маркеров

        Возвращает центр каждого маркера
        '''

        lst = []

        for i in bboxs:
            markers = i[0]
            a1, a2, a3, a4 = markers

            x1, y1 = a1
            x2, y2 = a2
            x3, y3 = a3
            x4, y4 = a4

            k1 = (y1-y3)/(x1-x3)
            k2 = (y2-y4)/(x2-x4)

            b1 = y1 - (y3- y1)/(x3-x1)*x1
            b2 = y2 - (y4-y2)/(x4-x2)*x2

            x_c = (b2-b1)/(k1-k2)
            y_c = k1*x_c + b1

            lst.append([y_c, x_c])

        return lst
    
    def get_temperature(self, exp_path):
        
        path= os.path.join(exp_path, 'metadata/temperature.txt')
        
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        if len(lines) == 0:
            self.temperature = [None, None, None, None]
        else:
            temperature = lines[0].split('\n')[0]
            temperature = temperature.split(';')
            temperature = [float(i) for i in temperature]

            self.temperature = temperature


    def add_tag(self, tag: str) -> None:
        """Добавить тег к объекту"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> bool:
        """Удалить тег, возвращает True если тег был удален"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Обновить пользовательские метаданные"""
        if self.custom_metadata is None:
            self.custom_metadata = {}
        self.custom_metadata[key] = value
    
    def get_metadata(self, key: str, default=None) -> Any:
        """Получить значение из пользовательских метаданных"""
        if self.custom_metadata:
            return self.custom_metadata.get(key, default)
        return default
    
    
    def deep_copy(self) -> 'SFDIStackMeasurement':
        """
        Creates a deep copy of this SFDIStackMeasurement instance.

        The deep copy handles the following attributes:
        - stack (SFDIStack): Uses the SFDIStack's deep copy method if available,
          otherwise performs manual deep copy of its components
        - white_img (Optional[np.ndarray]): Copied using np.copy() to create an independent array
        - aruco_coords (Optional[list]): Creates a deep copy of the list and its nested structures
        - temperature (Optional[list]): Creates a new list with the same values

        Returns:
            SFDIStackMeasurement: A new SFDIStackMeasurement instance with all attributes 
                deeply copied, completely independent from the original instance.

        """

        from copy import deepcopy

        if hasattr(self.stack, 'deep_copy'):
            stack_copy = self.stack.deep_copy()
        
        white_img_copy = np.copy(self.white_img) if self.white_img is not None else None
        aruco_coords_copy = deepcopy(self.aruco_coords) if self.aruco_coords is not None else None
        temperature_copy = list(self.temperature) if self.temperature is not None else None

        # Create and return the new SFDIStackMeasurement instance
        return SFDIStackMeasurement(
            stack=stack_copy,
            white_img=white_img_copy,
            glucose_mmol=self.glucose_mmol,
            aruco_coords=aruco_coords_copy,
            aruco_coords_mod=self.aruco_coords_mod,
            temperature=temperature_copy,
            date=self.date,
            time=self.time,
            roi_mask_corr = self.roi_mask_corr
        )
    def convert_time(self):
    
        lst = np.array([int(i) for i in self.time.split('-')])
        t = np.array([3600, 60, 1])*lst

        return t.sum()

    
    def get_glucose_values(self, glucose_interp):
        
        time = self.convert_time()
        self.glucose_mmol = glucose_interp(time)
        