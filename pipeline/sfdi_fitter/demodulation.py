from __future__ import annotations

from abc import ABC,abstractmethod
import sfdi_fitter.data as sd
from sfdi_fitter.data import SFDIStack
from typing import Optional, List, Union
import numpy as np
import scipy.ndimage as scnd
import warnings

try:
    import torch
    import torch.nn.functional as F
    from sfdi_fitter.models import ConvTanh, UNetGioux
except ImportError:
    torch = None
    F = None
    ConvTanh = None
    UNetGioux = None

class Processor(ABC):

    @abstractmethod
    def process(sfdi_stack:SFDIStack) -> SFDIStack:
        """
        Process the input SFDI stack and return the stack.

        Args:
            sfdi_stack (SFDIStack): The input SFDI stack to be processed.  
        """
        pass

def _put_along_axis(arr, indices_along_axis, v, axis):
    """

    """
    slices = [slice(None)]*arr.ndim
    slices[axis] = indices_along_axis
    arr[tuple(slices)] = v
    
class ClassicalDemodulator(Processor):

    def __init__(self,add_dc:bool=False,
                     phase_ids:Optional[List[int]]=None,
                     mdc_freq_id:Optional[int]=0):
        self.add_dc = add_dc
        self.phase_ids = phase_ids
        self.mdc_freq_id = mdc_freq_id
    
    def __repr__(self):
        return f"ClassicalDemodulator(add_dc={self.add_dc}, phase_ids={self.phase_ids}, mdc_freq_id={self.mdc_freq_id})"

    @staticmethod
    def _get_default_phase_ids(data:np.ndarray,phase_index:int,
                                phase_ids:Optional[List[int]]=None) -> List[int]:
        """
        Get the default phase IDs based on the shape of the input data.

        Args:
            data (np.ndarray): The input data array from which to determine the default phase IDs.
            phase_index (int): The index of the phase axis in the data array.
            phase_ids (Optional[List[int]]): The IDs of the phases to be used.

        Returns:
            List[int]: A list of default phase IDs corresponding to the number of phases in the data.
        """
        if phase_ids is not None:
            assert max(phase_ids) < data.shape[phase_index], "Phase IDs exceed the number of available phases in the data."
        else:
            phase_ids = list(range(data.shape[phase_index]))
        return phase_ids

    @staticmethod
    def calculate_mac(data:np.ndarray,
                    phase_axis_index:int, 
                    phase_ids:Optional[List[int]]=None) -> np.ndarray:
        """
        Calculate the Modulation Amplitude Component (MAC) from the input data.

        Args:
            data (np.ndarray): The input data array from which to calculate the MAC.
            phase_axis_index (int): The index of the phase axis in the data array.
            phase_ids (Optional[List[int]]): The IDs of the phases to be used for MAC calculation.
        Returns:
            np.ndarray: The calculated MAC values.
        """
        
        phase_ids = ClassicalDemodulator._get_default_phase_ids(data, phase_axis_index, phase_ids)
        phase_ids.sort()
        n = len(phase_ids)

        new_shape = list(data.shape)
        new_shape[phase_axis_index] = 1
        mac = np.zeros(new_shape, dtype=np.float32)

        for i in range(len(phase_ids)):
            pi = phase_ids[i]
            for j in range(i+1,len(phase_ids)):
                pj = phase_ids[j]
                res =  mac.take(0,axis=phase_axis_index) + (data.take(pi, axis=phase_axis_index) - data.take(pj, axis=phase_axis_index))**2 
                _put_along_axis(mac, 0, res, axis=phase_axis_index)

        mac = (2 ** 0.5 / n) * np.sqrt(mac)
        return mac
    
    @staticmethod
    def calculate_mdc(data:np.ndarray,
                      phase_axis_index:int,
                      frequency_axis_index:int,
                      mdc_freq_id:int=0,
                      phase_ids:Optional[List[int]]=None) -> np.ndarray:
        """
        Calculate the Modulation Depth Component (MDC) from the input data.

        Args:
            data (np.ndarray): The input data array from which to calculate the MDC.
            phase_axis_index (int): The index of the phase axis in the data array.
            frequency_axis_index (int): The index of the frequency axis in the data array.
            mdc_freq_id (int): The frequency index to be used for MDC calculation.
            phase_ids (Optional[List[int]]): The IDs of the phases to be used for MDC calculation.  
        Returns:
            np.ndarray: The calculated MDC values.      
        """

        phase_ids = ClassicalDemodulator._get_default_phase_ids(data, phase_axis_index, phase_ids)
        res = data.mean(axis=phase_axis_index, keepdims=True).take(mdc_freq_id, axis=frequency_axis_index)

        mdc_shape = list(data.shape)
        mdc_shape[phase_axis_index] = 1
        mdc_shape[frequency_axis_index] = 1
        
        mdc = np.zeros(mdc_shape, dtype=np.float32)
        _put_along_axis(mdc, 0, res, axis=frequency_axis_index)
        return mdc
        
    def process(self, sfdi_stack:SFDIStack) -> SFDIStack:
        """
        Process the input SFDI stack using the classical demodulation method.

        Args:
            sfdi_stack (SFDIStack): The input SFDI stack to be processed.

        Returns:
            SFDIStack: The processed SFDI stack after demodulation.
        """
        phase_axis_index = sfdi_stack.get_axis_index(sd.StackAxis.PHASE)
        mac = self.calculate_mac(sfdi_stack.data, phase_axis_index, self.phase_ids)

        spatial_frequencies = sfdi_stack.spatial_frequencies

        processed_data = mac
        if self.add_dc:
            frequency_axis_index = sfdi_stack.get_axis_index(sd.StackAxis.FREQUENCY)
            mdc = self.calculate_mdc(sfdi_stack.data, 
             phase_axis_index,
             frequency_axis_index,
             self.mdc_freq_id, self.phase_ids)

            if spatial_frequencies is not None:
                spatial_frequencies = [0] + list(sfdi_stack.spatial_frequencies)
            processed_data = np.concatenate((mdc, processed_data), axis=frequency_axis_index)

        return SFDIStack(data=processed_data, axis_names=sfdi_stack.axis_names, 
        spatial_frequencies=spatial_frequencies, wavelengths=sfdi_stack.wavelengths)


class SingleShotDemodulator(Processor, ABC):

    def __init__(self,add_dc:bool=True, mdc_freq_id:int=0):
        self.add_dc = add_dc
        self.mdc_freq_id = mdc_freq_id
    
    @abstractmethod
    def calculate_mac(self, img:np.ndarray) -> np.ndarray:
        """
        Calculate the Modulation Amplitude Component (MAC) from the input SFDI stack.

        Args:
            img (np.ndarray): The input image from which to calculate the MAC.
        Returns:
            np.ndarray: The calculated MAC values.
        """
        pass

    @abstractmethod
    def calculate_mdc(self, img:np.ndarray) -> np.ndarray:
        """
        Calculate the Modulation Depth Component (MDC) from the input SFDI stack.

        Args:
            img (np.ndarray): The input image from which to calculate the MDC.

        Returns:
            np.ndarray: The calculated MDC values.
        """
        pass

    def process(self, sfdi_stack:SFDIStack) -> SFDIStack:
        """
        Process the input SFDI stack using the single-shot demodulation method.
        """

        if sd.StackAxis.FREQUENCY not in sfdi_stack.axis_names:
            sfdi_stack.data = np.expand_dims(sfdi_stack.data, axis=0)
            sfdi_stack.axis_names = [sd.StackAxis.FREQUENCY] + sfdi_stack.axis_names
            sfdi_stack.reorder_axes(sfdi_stack.get_standard_axis_order(),inplace=True)
        
        non_coord_axes = sfdi_stack.get_noncoord_axes()

        _frequency_index = sfdi_stack.get_axis_index(sd.StackAxis.FREQUENCY)

        data_shape = list(sfdi_stack.data.shape)

        if self.add_dc:
            data_shape[_frequency_index] = data_shape[_frequency_index] + 1
        
        macs = np.empty(data_shape, dtype=np.float32)

        for _indices, single_shot in sfdi_stack.iterate_over_axes(*non_coord_axes):

            _indices = list(_indices)

            if _indices[_frequency_index] == self.mdc_freq_id and self.add_dc:
                macs[tuple(_indices)] = self.calculate_mdc(single_shot)

            if self.add_dc:
                _indices[_frequency_index] = _indices[_frequency_index]  + 1
            
            macs[tuple(_indices)] = self.calculate_mac(single_shot)

        
        spatial_frequencies = []
        if sfdi_stack.spatial_frequencies is None:
            _id = sfdi_stack.get_axis_index(sd.StackAxis.FREQUENCY)
            n = sfdi_stack.shape[_id]
            spatial_frequencies = range(1,n+1)
            warnings.warn("SFDI stack doesn't contain frequencies. Adding spatial frequencies manually...")
        else:    
            spatial_frequencies = list(sfdi_stack.spatial_frequencies)

        if self.add_dc:
            spatial_frequencies = [0] + spatial_frequencies
        
        return SFDIStack(data=macs, axis_names=sfdi_stack.axis_names,
                     spatial_frequencies=spatial_frequencies,
                     parameter_names=sfdi_stack.parameter_names, wavelengths=sfdi_stack.wavelengths)

class CosConvolveDemodulator(SingleShotDemodulator):

    def __init__(self, convolution_period: float, add_dc:bool=True, mdc_freq_id:int=0):
        super().__init__(add_dc, mdc_freq_id)
        self.convolution_period = convolution_period

    def __repr__(self):
        return f"""CosConvolveDemodulator(convolution_period={self.convolution_period},
                                          add_dc={self.add_dc}, mdc_freq_id={self.mdc_freq_id})"""
        
    def calculate_mac(self, img: np.ndarray) -> np.ndarray:
        """
        Calculate the Modulation Amplitude Component (MAC) from the input image using cosine convolution.

        Args:
            img (np.ndarray): The input image from which to calculate the MAC.
        Returns:
            np.ndarray: The calculated MAC values.
        """   
        T = self.convolution_period
        x = np.arange(T,dtype=np.float32)
        fx = 1./T
        kernel_cosx = np.cos(2 * np.pi * fx * x)
        kernel_sinx = np.sin(2 * np.pi * fx * x)
        kernel_ones = (1/T)*np.ones_like(kernel_cosx)
        norm_factor = np.sum(kernel_cosx**2)

        conv_cos = scnd.convolve1d(img, kernel_cosx, axis=1,mode='reflect')
        conv_cos = scnd.convolve1d(conv_cos, kernel_ones, axis=0, mode='reflect')
        conv_sin = scnd.convolve1d(img, kernel_sinx,axis=1, mode='reflect')
        conv_sin = scnd.convolve1d(conv_sin, kernel_ones, axis=0, mode='reflect')

        norm_factor = np.sum(kernel_cosx**2)
        mac = np.sqrt(conv_cos**2 + conv_sin**2) / norm_factor

        return mac


    def calculate_mdc(self, img:np.ndarray) -> np.ndarray:
        """
        Calculate the Modulation Depth Component (MDC) from the input image using cosine convolution.

        Args:
            img (np.ndarray): The input image from which to calculate the MDC.
        """
        T = self.convolution_period
        kernel_ones = (1/T)*np.ones(T, dtype=np.float32)
        conv = scnd.convolve1d(img, kernel_ones, axis=1, mode='reflect')
        mdc = scnd.convolve1d(conv, kernel_ones, axis=0, mode='reflect')
        return mdc
    

def _torch_no_grad(func):
    if torch is None:
        return func
    return torch.no_grad()(func)


class UNetDemodulator(SingleShotDemodulator):
    """
    Single-shot demodulator based on UNet network

    args:
        weights_path: path to saved weights (state_dict)
        device: 'cpu' or 'cuda'
        in_ch: number of input channels
        out_ch: number of output channels (2 = [DC, AC])
        base_ch: number of UNet base channels
        line_mode: 1D-convolution mode
        norm: normalization type ('bn', 'gn', 'in', None)
        add_dc: either adding DC component to output
        mdc_freq_id: frequency index to get DC
        mdc_channel_index: which output channel for DC
        mac_channel_index: which output channel for AC
    """

    def __init__(
        self,
        weights_path: str,
        device: str = "cuda",
        in_ch: int = 1,
        out_ch: int = 4,
        base_ch: int = 8,
        line_mode: bool = False,
        norm: Optional[str] = "bn",
        add_dc: bool = True,
        mdc_freq_id: int = 0,
        mdc_channel_index: int = 0,
        mac_channel_index: int = 1,
    ):
        super().__init__(add_dc=add_dc, mdc_freq_id=mdc_freq_id)

        if torch is None or UNetGioux is None:
            raise ImportError("UNetDemodulator requires torch")

        self.device = torch.device(device)
        self.mdc_channel_index = mdc_channel_index
        self.mac_channel_index = mac_channel_index
        self.weights_path = weights_path

        self.model = UNetGioux(
            in_ch=in_ch, out_ch=out_ch,
            base_ch=base_ch, line_mode=line_mode, norm=norm,
        )

        state_dict = torch.load(weights_path, map_location=self.device, weights_only=True)
        if any(k.startswith("module.") for k in state_dict):
            state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
        self.model.load_state_dict(state_dict)

        self.model.to(self.device)
        self.model.eval()

    def __repr__(self):
        return (
            f"UNetDemodulator(weights_path='{self.weights_path}', "
            f"device='{self.device}', add_dc={self.add_dc})"
        )
    
    def _decode_output(self, y: torch.Tensor, eps: float = 1e-8):
        """
        y: [B,4,H,W] raw = [DC_raw, AC_raw, u_raw, v_raw]
        returns: dc, ac, cos_phi, sin_phi, phi  (all [B,1,H,W])
        """
        dc_raw = y[:, 0:1]
        ac_raw = y[:, 1:2]
        u_raw  = y[:, 2:3]
        v_raw  = y[:, 3:4]

        dc = F.softplus(dc_raw)
        ac = F.softplus(ac_raw)

        norm = torch.sqrt(u_raw * u_raw + v_raw * v_raw + eps)
        cos_phi = u_raw / norm
        sin_phi = v_raw / norm
        phi = torch.atan2(sin_phi, cos_phi)

        return dc, ac, cos_phi, sin_phi, phi

    @_torch_no_grad
    def _run_model(self, img: np.ndarray):
        """
        img: (H, W)
        returns dict with decoded maps
        """
        x = torch.from_numpy(img.astype(np.float32))[None, None, :, :].to(self.device)  # [1,1,H,W]
        y = self.model(x) 

        dc, ac, cos_phi, sin_phi, phi = self._decode_output(y)

        return {
            "dc": dc[0, 0].cpu().numpy(),
            "ac": ac[0, 0].cpu().numpy(),
            "cos_phi": cos_phi[0, 0].cpu().numpy(),
            "sin_phi": sin_phi[0, 0].cpu().numpy(),
            "phi": phi[0, 0].cpu().numpy(),
        }

    def calculate_mac(self, img: np.ndarray) -> np.ndarray:
        """
        img: (H, W) — raw SFDI-frame
        returns: (H, W) — MAC
        """
        out = self._run_model(img)
        return out["ac"]

    def calculate_mdc(self, img: np.ndarray) -> np.ndarray:
        """
        img: (H, W) — raw SFDI-frame
        returns: (H, W) — MDC
        """
        out = self._run_model(img)
        return out["dc"]
