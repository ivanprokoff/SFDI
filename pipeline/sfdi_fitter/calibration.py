import pandas as pd
import numpy as np
import scipy.interpolate as scinterp
from pathlib import Path


### The absorption values are calculated experimentally
# reduced scattering coefficients are taken from
# Di Ninni, Paola, et al. "Fat emulsions as diffusive reference standards
# for tissue simulating phantoms?." Applied Optics 51.30 (2012): 7176-7182.
###

def _asset_path(filename):
    package_asset_path = Path(__file__).resolve().parent / 'assets' / filename
    parent_asset_path = Path(__file__).resolve().parents[1] / 'assets' / filename

    for path in (package_asset_path, parent_asset_path):
        if path.exists():
            return str(path)

    return str(package_asset_path)


_NIGROSIN_ABSORPTION_PATH = _asset_path('NIGROSIN_EXCTINCTION.csv')
_LIPOFUNDIN_SCATTERING_PATH = _asset_path('LIPOFUNDIN_SCATTERING.csv')

def _load_reference_data(path):
    """

    :param path:
    :return:
    """
    return pd.read_csv(path,index_col=0)

NIGROSIN_EXTINCTION = _load_reference_data(_NIGROSIN_ABSORPTION_PATH)
LIPOFUNDIN_REDUCED_SCATTERING = _load_reference_data(_LIPOFUNDIN_SCATTERING_PATH)


def _get_lipofundin_reduced_scattering_interpolation():
    df = LIPOFUNDIN_REDUCED_SCATTERING
    
    wvs = df.index.values
    scat = df.values[:,0]
    
    return scinterp.interp1d(wvs,scat)

def _get_nigrosin_extinction_interpolation():
    df = NIGROSIN_EXTINCTION
    
    wvs = df.index.values
    scat = np.log(10)*df.values[:,0]/10
    
    return scinterp.interp1d(wvs,scat)

nigrosin_mua_ext_inv_mm = _get_nigrosin_extinction_interpolation()
lipofundin_reduced_scattering_interp_invmm = _get_lipofundin_reduced_scattering_interpolation()


def get_mua(nigrosin_concentration, central_wavelength=560, delta=10):
    """
    calculate mean absorption coefficient for e-base logarithm
    for given nigrosin_concentration in mg/ml in spectral range
    (central_wavelength-delta/2,central_wavelength+delta/2)

    :param nigrosin_concentration: (float) in mg/ml
    :param central_wavelength: (float) in nm
    :param delta: (float) width of spectral range

    :return (float) e-based absorption coefficient in mm^{-1} for nigrosin
    """
    exct = NIGROSIN_EXTINCTION[central_wavelength - delta / 2:central_wavelength + delta / 2].mean()

    return nigrosin_concentration * exct.values[0] * np.log(10) / 10


def get_mus(lipofundin_volume_fraction, central_wavelength=560, delta=10):
    """
    calculate e-based mean reduced scattering coefficient
    for given Lipofundin-S 20% volume concentration in (lipofundin volume/total_volume)
    in spectral range (central_wavelength-delta/2,central_wavelength+delta/2)

    :param lipofundin_volume_fraction: (float) volume fraction of Lipofundin 20% in %volume/%volume
    :param central_wavelength: (float) in nm
    :param delta: (float) width of spectral range

    :return (float) e-based reduced scattering coefficient in mm^{-1} for lipofundind
    """
    exct = LIPOFUNDIN_REDUCED_SCATTERING[central_wavelength - delta / 2:central_wavelength + delta / 2].mean()

    return lipofundin_volume_fraction*exct.values[0]
