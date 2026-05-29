import numpy as np
import scipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
import  matplotlib.patches as mpatch
from typing import Tuple,Optional
import skimage.filters as skfilt
import tqdm
import math

import glob
import os
import sys
sys.path.append('/2tb_drive/old_data/notebooks/Ilia/Glucosa/SFDI/')

import sfdi_config


import skimage.io as skio
import sfdi_fitter.preprocess as preprocess
import sfdi_fitter.fitter as fitter
import importlib
importlib.reload(preprocess)
importlib.reload(fitter)

import IB_ssmd_demodulation as ssmd
import IB_hilbert_demodulation as hd


import lab_tools.plot_utils as pu
pu.load_figure_style()

import sfdi_fitter.utils as sfdi_utils
import sfdi.sfdi_fitter.calibration as sfdi_calibration
importlib.reload(fitter)

def get_sample_name(sample_folder):
    return sample_folder.split('/')[-2]

def get_wavelength(sample_folder):
    return os.path.basename(sample_folder)

def get_full_name(sample_folder):
    
    sample_name = get_sample_name(sample_folder)
    wavelength = get_wavelength(sample_folder)
    name = f'{sample_name}_wv={wavelength}'
    
    return name

def draw_rectangle(bot:int,top:int,left:int,right:int,color='r',
                  ax=None):
    if ax is None:
        ax = plt.gca()
    width = right-left
    height = top-bot
    
    rect = mpatch.Rectangle(xy=(left,bot),width=width,height=height,color=color,
                           fill=None,linewidth=1.5)
    ax.add_patch(rect)
    
    return rect

def color_name_to_wavelength_nm(color_name):
    if color_name == 'red':
        return 634
    if color_name == 'green':
        return 548
    if color_name == 'blue':
        return 451
    
    raise ValueError(f"Color {color_name} is unknown")
    
def get_full_name(sample_folder):
    sample_name = get_sample_name(sample_folder)
    wavelength = get_wavelength(sample_folder)
    name = f'{sample_name}_wv={wavelength}'
    
    return name

def parse_sample_name(sample_name):
    sample_id,mua_str,mus_str = sample_name.split('_')[:3]
    mua = float(mua_str.split('=')[-1])
    mus = float(mus_str.split('=')[-1])
    
    return sample_id,mua,mus

def get_mua_mus(sample_name,wavelength_name,calibration_wavelength_nm=550.):
    
    if type(wavelength_name) == str:
        wv_nm = color_name_to_wavelength_nm(wavelength_name)
    else:
        wv_nm = wavelength_name
        
    sample_id,mua,mus = parse_sample_name(sample_name)
    
    mua_660_phantom = mua/10 #to inv mm from inv cm
    mus_751_phantom =mus/10 #to inv mm from inv cm
    
    mua_on_wv = sfdi_calibration.nigrosin_mua_ext_inv_mm(wv_nm)
    mua_on_660 = sfdi_calibration.nigrosin_mua_ext_inv_mm(calibration_wavelength_nm)
    
    mus_on_wv = sfdi_calibration.lipofundin_reduced_scattering_interp_invmm(wv_nm)
    mus_on_751 = sfdi_calibration.lipofundin_reduced_scattering_interp_invmm(calibration_wavelength_nm)
    
    mua = mua_on_wv/mua_on_660*mua_660_phantom
    mus = mus_on_wv/mus_on_751*mus_751_phantom
    return mua,mus

def get_mask_for_phantom(binned_mac,fit_mask_coords):
    mask = np.zeros_like(binned_mac[0],dtype=np.bool_)
    _fit_bot,_fit_top,_fit_left,_fit_right = fit_mask_coords
    mask[_fit_bot:_fit_top,_fit_left:_fit_right]= True
    return mask

def get_intensity_profile(phase_img:np.ndarray,coords:Tuple[int,int,int,int]) -> np.ndarray:
    bot,top,left,right = coords
    return np.nanmean(phase_img[bot:top,left:right],axis=0)

def read_and_preprocess_using_different_agorithm(demodulation_method, sample_folder,
                                                binning_kernel_size, verbose):
    
    '''
        Использует разные методы демодуляции:
        
        ['classic', 'ssmd', 'ssop', 'hilbert']
        
    '''
    
    if demodulation_method == 'classic':
        
        test_freqs, binned_mac = preprocess.read_and_preprocess(
                sample_folder,binning_kernel_size=binning_kernel_size,
                verbose=False)
        
    elif demodulation_method == 'ssmd_normal':
        
        test_freqs, binned_mac = ssmd.read_and_preprocess(
                sample_folder, demodulation_mode='normal', binning_kernel_size=binning_kernel_size,
                verbose=False)
        
    elif demodulation_method == 'ssmd_fast':
        
        test_freqs, binned_mac = ssmd.read_and_preprocess(
                sample_folder, demodulation_mode = 'fast', binning_kernel_size=binning_kernel_size,
                verbose=False)
        
        
    elif demodulation_method == 'hilbert':
        
        test_freqs, binned_mac = hd.read_and_preprocess(
                sample_folder,binning_kernel_size=binning_kernel_size,
                verbose=False)
        
    return test_freqs, binned_mac
        

def get_reference_phantoms(reference_path:str, demodulation_method:str, reference_mua_mus:dict[str,[float,float]],
                           wavelengths_colors=['red','green','blue'],
                          verbose:bool=True, binning_kernel_size=9,
                           fit_mask_coords:Tuple[int,int,int,int]=(0,600,0,400)):
    '''
    Получает путь референсного фантома и возвращает соответствующий словарь
    '''
    
    reference_phantoms = {}
    
    for wavelength in wavelengths_colors:
        reference_sample_folder = os.path.join(reference_path,wavelength)
        
        ref_freqs, ref_binned_mac = read_and_preprocess_using_different_agorithm(sample_folder=reference_sample_folder,
                                                  binning_kernel_size=binning_kernel_size, demodulation_method = demodulation_method,
                                                  verbose=False)

        reference_phantoms[wavelength] = ref_freqs,ref_binned_mac
        
    if verbose:
        print(f"Reading reference from {reference_path}")
        plt.figure(figsize=(15,5))
        
        
        for i,wavelength in enumerate(wavelengths_colors):
            _freqs,_mac = reference_phantoms[wavelength]
            plt.subplot(1,3,i+1)
            plt.imshow(_mac[0])
            draw_rectangle(*fit_mask_coords)
            mua,mus = reference_mua_mus[wavelength]
            plt.title(f"MAC at {wavelength}\n mua = {mua:.3f} mm-1\nmus' = {mus:.3f} mm-1")
        
        plt.show()
        
    return reference_phantoms, ref_freqs
    

def fit_folder(sample_folders:list[str],
               reference_path:str, reference_mua_mus:dict[str,[float,float]],
                   fit_mask_coords:Tuple[int,int,int,int]=(0,600,0,400), demodulation_method='classic',
               object_height_mm=0., verbose:bool=True, 
               binning_kernel_size=9,wavelengths_colors=['red','green','blue'],
              freq_indices_to_use:Optional[list]=None):
    
    reference_phantoms, ref_freqs = get_reference_phantoms(reference_path=reference_path, demodulation_method=demodulation_method,
                reference_mua_mus = reference_mua_mus, wavelengths_colors=wavelengths_colors,
                verbose=verbose, binning_kernel_size=binning_kernel_size, fit_mask_coords=fit_mask_coords)
    
    indices_to_use = [i for i in range(len(ref_freqs))]
    
    if freq_indices_to_use:
        indices_to_use = freq_indices_to_use
    
    
    diffuse_model = fitter.MCML_model(spatial_frequencies=sfdi_utils.calculate_real_frequencies_from_prepends(ref_freqs,
                                      object_height_mm=object_height_mm),
                                      freq_prepends_calibration_slope=sfdi_utils._FREQUENCY_PREPENDS_CALIBRATION_SLOPE)
    
    results = {}
    rs = {}
    
    for sample_folder in tqdm.tqdm_notebook(sample_folders):
        
        sample_name = get_sample_name(sample_folder)
        wavelength = get_wavelength(sample_folder)

        name = get_full_name(sample_folder)
        mua_ref,mus_ref = reference_mua_mus[wavelength]

        ref_freqs,ref_binned_mac = reference_phantoms[wavelength]

        #read and preprocessing the input sample
        try:
            test_freqs, binned_mac = read_and_preprocess_using_different_agorithm(demodulation_method=demodulation_method,
                                                                                 sample_folder=sample_folder,
                                                                                binning_kernel_size=binning_kernel_size,
                                                                                 verbose=False)
            
        except ValueError:
            print(f'Error on processing : {sample_folder}')
            continue
            
        spatial_frequencies = sfdi_utils.calculate_real_frequencies_from_prepends(test_freqs,
                                                                                 object_height_mm=object_height_mm)
        spatial_frequencies_ref = sfdi_utils.calculate_real_frequencies_from_prepends(ref_freqs,object_height_mm=object_height_mm)

        reflectance_stack = fitter.get_reflectance_stack(freqs_test=spatial_frequencies,
                              mac_test=binned_mac,
                              freqs_reference=spatial_frequencies_ref,
                              mac_reference=ref_binned_mac,
                                                 ref_mua=mua_ref,
                                                 ref_mus_prime=mus_ref, model=diffuse_model)


        ref_mask  = get_mask_for_phantom(ref_binned_mac,fit_mask_coords)
        test_mask = get_mask_for_phantom(binned_mac,fit_mask_coords)
        fit_mask = ref_mask&test_mask
        
        reflectance_stack[:,~fit_mask] = np.nan
        

        if verbose:
            print('Spatial frequencies in mm^{-1} are',spatial_frequencies)
            print(f"Sample name: {name}")
            _vmin = 0.01 #np.percentile(reflectance_stack[:,phantom_mask].ravel(),1)
            _vmax = 0.8 #np.percentile(reflectance_stack[:,phantom_mask].ravel(),99)


            plt.figure(figsize=(25,10))
            for i,refl in enumerate(reflectance_stack):
                plt.subplot(2,5,i+1)
                plt.imshow(refl,vmin=0,vmax=1)
                draw_rectangle(*fit_mask_coords)
            plt.show()    

            plt.figure(figsize=(25,10))
            for i,refl in enumerate(reflectance_stack):
                plt.subplot(2,5,i+1)

                plt.plot(get_intensity_profile(refl,fit_mask_coords))


            plt.figure(figsize=(8,5))
            mu = np.mean(reflectance_stack[:,fit_mask],axis=1)
            sd = np.std(reflectance_stack[:,fit_mask],axis=1)
            plt.plot(spatial_frequencies,mu,color='b')
            plt.fill_between(spatial_frequencies,mu-sd,mu+sd,alpha=0.3,color='b')
            plt.xlabel("Spatial frequency, mm^{-1}")
            plt.ylabel("Mean reflectance")
            for i,r in enumerate(reflectance_stack):
                if i%5 == 0:
                    plt.figure(figsize=(20,4))

                plt.subplot(1,5,i%5 + 1)
                plt.imshow(r,vmin=_vmin,vmax=_vmax)
                plt.title(f'Spatial frequency\nk ={spatial_frequencies[i]:.2f}' + r', $\rm mm^{-1}$')

                plt.colorbar()

                if i%5 == 4 or i == reflectance_stack.shape[0]-1:
                    plt.show()
                    plt.tight_layout()


        fit_results = fitter.fit_diffuse_reflectance_stack(spatial_frequencies[indices_to_use],
                                                           reflectance_stack[indices_to_use],
                                      fit_mask=fit_mask,model=diffuse_model,
                                                           mode='LUT',
                                                           backend='cpp')

        fit_results['fit_mask'] = fit_mask
        #print(name)
        results[name] = fit_results
        rs[name] = reflectance_stack
        
    #print(results.keys())
    return {'fit_results':results,
             'fit_df':dict_to_fit_df(results),
            'reflectance_stacks':rs,
            'reference_phantom':reference_phantoms}


def dict_to_fit_df(results,global_roi_coords=None):
    fit_df = {k:[] for k in ['mua','mus','name']}
    
    use_global_roi = not global_roi_coords is None
        
    for name, result in results.items():
        
        if not use_global_roi:
            fit_mask = result['fit_mask']
            
        for i,par in enumerate(['mua','mus']):
            if not use_global_roi:
                result[par] = result[par][:, :]
                result[par][~fit_mask] = np.nan

                img = result[par][fit_mask]
                fit_df[par].extend(img.ravel().tolist())
            else:
                bot,top,left,right = global_roi_coords
                img = result[par][bot:top,left:right]
                fit_df[par].extend(img.ravel())
                
        fit_df['name'].extend([name]*img.ravel().shape[0])
    return pd.DataFrame(fit_df)