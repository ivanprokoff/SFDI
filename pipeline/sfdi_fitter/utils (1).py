import sfdi_fitter.calibration as calibration
import numpy as np

def get_mua_mus(sample_name, wavelength, water_volume=1000., wv_delta=10.,stock_nigrosin_concentration_mg_ml=0.8):
    """
    Calculate mua and mus in mm^{-1} using phantom sample_name and central_wavelength
    for specific type of sample_name

    :param sample_name (str): sample name in format '070_090' where 070 is the volume of LipofundinS20 solution in ul
    and 090 is the volume of nigrosin in ul
    :param wavelength (str): '560' or '630' wavelength in nm for concentration
    :param water_volume(float, default=1000.): volume of water in phantom solution in ul
    :param wv_delta (float, default=10.):
    :param stock_nigrosin_concentration_mg_ml (float): stock nigrosin concentration used to prepare phantom solutino

    :return: mua and mus
    """
    volume_nig, volume_lip = map(float, sample_name.split('_'))
    total_volume = volume_nig + volume_lip + water_volume
    conc_nig = stock_nigrosin_concentration_mg_ml * volume_nig / total_volume
    conc_lip = volume_lip / total_volume

    mua = calibration.get_mua(conc_nig, central_wavelength=int(wavelength), delta=wv_delta)
    mus = calibration.get_mus(conc_lip, central_wavelength=int(wavelength), delta=wv_delta)
    return mua, mus


def get_freqs_in_mm_from_prepends(freq_prepends):
    """
    calculate real spatial frequencies k = 2pi/L from frequencies prepends
    extracted from filenames given in arbitrary units

    :param freq_prepends: list of spatial frequency prepends extracted from filenames
    in arbitrary units
    :return (np.array): numpy array of spatial frequencies given
    """

    return 2 * np.pi * np.array([float(x) / 155. for x in freq_prepends])


_FREQUENCY_PREPENDS_CALIBRATION_SLOPE = 0.03796611

def calculate_real_frequencies_from_prepends(freq_prepends:list,
                                             object_height_mm:float=0.,
                                             projector_heigth_mm:float=200.,
                                             calibration_slope_zero_height:float=_FREQUENCY_PREPENDS_CALIBRATION_SLOPE):
    """Calculates real spatial frequencies from frequency prepends with height correction.
    
    Converts frequency prepends to real spatial frequencies (k = 2π/L) by applying
    a calibration slope and correcting for object height relative to the projector.
    
    Args:
        freq_prepends: Array-like of frequency prepend values to convert
        object_height_mm: Height of the object in millimeters. Defaults to 0.0.
        projector_heigth_mm: Height of the projector in millimeters. Defaults to 200.0.
        calibration_slope_zero_height: Slope calibration factor at zero height between freq_prepends and real freqs in inv_mm
            Defaults to 0.3796611.
    
    Returns:
        ndarray: Real spatial frequencies in mm-1 accounting for height correction.
        
    Note:
        - The spatial frequencies are 2*π/T
        - The height correction factor accounts for perspective distortion based on
          the relative positions of the object and projector.
    """
    slope = calibration_slope_zero_height
    zero_height_k = np.array([slope*float(x) for x in freq_prepends])
    
    height_correction_factor = projector_heigth_mm/(projector_heigth_mm - object_height_mm)
    
    return height_correction_factor*zero_height_k