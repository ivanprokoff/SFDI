import numpy as np
import scipy.ndimage as scnd

from sfdi_fitter.demodulation import Processor
import sfdi_fitter.data as sd
import scipy.ndimage as scnd
from sfdi_fitter.display import NotebookDisplayMixin

class StackSqueezer(Processor,NotebookDisplayMixin):

    def __init__(self, inplace:bool=False):
        self.inplace = inplace

    def __repr__(self):
        return f"StackSqueezer(inplace={self.inplace})"

    def process(self,sfdi_stack:sd.SFDIStack) -> sd.SFDIStack:
        return sfdi_stack.squeeze(inplace=self.inplace)

class SelectIds(Processor,NotebookDisplayMixin):
    """
    This processor allows you to select specific indices along a specified axis of the SFDI stack.  
    """

    def __init__(self, axis:sd.StackAxis, ids:list):
        """
        initialize the SelectIds processor.
        Args:
            axis (sd.StackAxis): The axis along which to select the specified indices.
            ids (list): A list of indices to select along the specified axis.
        """
        self.axis = axis
        self.ids = ids

    def __repr__(self):
        return f"SelectIds(axis={self.axis}, ids={self.ids})"

    def process(self, sfdi_stack:sd.SFDIStack) -> sd.SFDIStack:
        axis_index = sfdi_stack.get_axis_index(self.axis)
        slices = [slice(None)]*sfdi_stack.data.ndim
        slices[axis_index] = self.ids
        selected_data = sfdi_stack.data[tuple(slices)]
        
        return sd.SFDIStack(data=selected_data, axis_names=sfdi_stack.axis_names,
                            spatial_frequencies=sfdi_stack.spatial_frequencies,
                            parameter_names=sfdi_stack.parameter_names,
                            wavelengths=sfdi_stack.wavelengths)
    
class Clipper(Processor,NotebookDisplayMixin):

    def __init__(self, clip_min:float=0., clip_max:float=1000.):
        self.clip_min = clip_min
        self.clip_max = clip_max

    def __repr__(self):
        return f"Clipper(clip_min={self.clip_min}, clip_max={self.clip_max})"

    def process(self, sfdi_stack:sd.SFDIStack) -> sd.SFDIStack:
        clipped_data = np.clip(sfdi_stack.data, self.clip_min, self.clip_max)
        return sd.SFDIStack(data=clipped_data, axis_names=sfdi_stack.axis_names,
                            spatial_frequencies=sfdi_stack.spatial_frequencies,
                            parameter_names=sfdi_stack.parameter_names,
                            wavelengths=sfdi_stack.wavelengths)

class MeanSmoother(Processor,NotebookDisplayMixin):

    def __init__(self,kernel_size:int=3,drop_intermediate:bool=False):
        self.kernel_size = kernel_size
        self.drop_intermediate = drop_intermediate
        self.kernel_1d = (1./self.kernel_size)*np.ones(self.kernel_size)
        
    def __repr__(self):
        return f"MeanSmoother(kernel_size={self.kernel_size}, drop_intermediate={self.drop_intermediate})"  
        
    def process(self, sfdi_stack:sd.SFDIStack) -> sd.SFDIStack:
        
        conv = scnd.convolve1d(sfdi_stack.data,self.kernel_1d,axis=sfdi_stack.get_axis_index(sd.StackAxis.X))
        res  = scnd.convolve1d(conv,self.kernel_1d,axis=sfdi_stack.get_axis_index(sd.StackAxis.Y))
        slices = [slice(None)]*sfdi_stack.data.ndim

        if self.drop_intermediate:
            for _axis in [sd.StackAxis.X,sd.StackAxis.Y]:
                _id = sfdi_stack.get_axis_index(_axis)
                slices[_id] = slice(self.kernel_size//2,None,self.kernel_size//2)
        
        return sd.SFDIStack(data=res[tuple(slices)],
                            spatial_frequencies=sfdi_stack.spatial_frequencies,
                            parameter_names=sfdi_stack.parameter_names,
                            wavelengths=sfdi_stack.wavelengths,
                            axis_names=sfdi_stack.axis_names)