from sfdi_fitter.fitter import get_reflectance_stack,ReflectanceModel
from sfdi_fitter.demodulation import Processor
import sfdi_fitter.data as sd
import numpy as np
from typing import Optional, Union
from sfdi_fitter.display import NotebookDisplayMixin

class ReflectanceCalculator(Processor,NotebookDisplayMixin):

    def __init__(self, reference_stack:sd.SFDIStack, reflectance_model:ReflectanceModel,
                ref_mua:Union[float,dict[str,float]]=1., 
                ref_mus_prime:Union[float,dict[str,float]]=10., refractive_index:float=1.37):
        """Initialize the ReflectanceCalculator.
            Args:
                reference_stack (SFDIStack): The reference SFDI stack to be used for reflectance calculation. 
                                                Must have the same axis names and data shape as the input SFDI stack.
                reflectance_model (ReflectanceModel): The reflectance model to be used for calculating reflectance.
                ref_mua (Union[float, dict[str, float]]): The absorption coefficient (mua) of the reference medium. 
                                    Can be a single float value or a dictionary mapping wavelengths to mua values.
                ref_mus_prime (Union[float, dict[str, float]]): The reduced scattering coefficient (mus') of the reference medium. 
                                    Can be a single float value or a dictionary mapping wavelengths to mus' values.
                refractive_index (float): The refractive index of the medium. Defaults to 1.37.
        """
        self.reference_stack = reference_stack
        self.model = reflectance_model
        self.ref_mua = ref_mua
        self.ref_mus_prime = ref_mus_prime
        self.refractive_index = refractive_index

        self._check_axis_requirements(reference_stack)

    def __repr__(self): 
        return "ReflectanceCalculator(reflectance_model={}, ref_mua={}, ref_mus_prime={}, refractive_index={})".format(
            self.model.__class__.__name__, self.ref_mua, self.ref_mus_prime, self.refractive_index)
        
    def _check_axis_requirements(self, sfdi_stack:sd.SFDIStack):
        required_axes = [sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y]
        if not all(axis in sfdi_stack.axis_names for axis in required_axes):
            raise ValueError(f"Input SFDI stack must include {required_axes}.")
        
    def _get_type_of_calculation(self, sfdi_stack:sd.SFDIStack) -> str:
        if sfdi_stack.axis_names == [sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y]\
            and self.reference_stack.axis_names == [sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y]:
            return "direct"
        elif sfdi_stack.axis_names == [sd.StackAxis.WAVELENGTH,sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y] and \
                self.reference_stack.axis_names == [sd.StackAxis.WAVELENGTH, sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y]:
            return "wavelength"
        else:
            raise ValueError("""Input SFDI stack and reference stack must have compatible 
                                axis names for reflectance calculation. Now
                                SFDI stack axis names: {}, 
                                reference stack axis names: {}""".format(
                                    sfdi_stack.axis_names, self.reference_stack.axis_names))
            
    def process(self, sfdi_stack:sd.SFDIStack) -> sd.SFDIStack:
        
        if not all(axis in sfdi_stack.axis_names for axis in [sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y]):
            raise ValueError("Input SFDI stack must include [sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y].")
        
        if sfdi_stack.spatial_frequencies is None:
            raise ValueError("ReflectanceCalculator requires spatial_frequencies for processing")

        if sfdi_stack.axis_names != self.reference_stack.axis_names:
            raise ValueError("Input SFDI stack and reference stack must have the same axis names.")

        if sfdi_stack.data.shape != self.reference_stack.data.shape:
            raise ValueError("Input SFDI stack and reference stack must have the same data shape.")
        
        self._check_axis_requirements(sfdi_stack)

        calculation_type = self._get_type_of_calculation(sfdi_stack)
        if calculation_type == "direct":
            # If both stacks have the same axis order, we can directly compute reflectance without reordering
            reflectance_data = get_reflectance_stack(sfdi_stack.spatial_frequencies,
                                                        sfdi_stack.data, 
                                                        self.reference_stack.spatial_frequencies, 
                                                        self.reference_stack.data, ref_mua=self.ref_mua,
                            ref_mus_prime=self.ref_mus_prime, refractive_index=self.refractive_index, model=self.model)

            
        elif calculation_type == "wavelength":
            _stack_iterator = sfdi_stack.iterate_over_axes(sd.StackAxis.WAVELENGTH)
            _ref_stack_iterator = self.reference_stack.iterate_over_axes(sd.StackAxis.WAVELENGTH)

            reflectance_data = np.empty_like(sfdi_stack.data)
            
            if sfdi_stack.wavelengths is None:
                raise ValueError("Input SFDI stack must have wavelengths defined for wavelength-based reflectance calculation.")
            
            for (wv_id, stack_slice), (_, ref_stack_slice) in zip(_stack_iterator, _ref_stack_iterator):
                wv_id = wv_id[0]
                wv = sfdi_stack.wavelengths[wv_id]

                reflectance_data_slice = get_reflectance_stack(sfdi_stack.spatial_frequencies,
                                                                stack_slice, 
                                                                self.reference_stack.spatial_frequencies, 
                                                                ref_stack_slice, ref_mua=self.ref_mua[wv],
                            ref_mus_prime=self.ref_mus_prime[wv], refractive_index=self.refractive_index, model=self.model)
                reflectance_data[wv_id] = reflectance_data_slice

        return sd.SFDIStack(data=reflectance_data, 
                            axis_names=sfdi_stack.axis_names, 
                            spatial_frequencies=sfdi_stack.spatial_frequencies,
                            parameter_names=sfdi_stack.parameter_names,
                            wavelengths=sfdi_stack.wavelengths)
        

class ReflectanceFitter(Processor,NotebookDisplayMixin):

    def __init__(self, reflectance_model:ReflectanceModel):
        self.reflectance_model = reflectance_model

    def __repr__(self):
        return f"ReflectanceFitter(reflectance_model={self.reflectance_model.__class__.__name__})"
    
    def _get_type_of_calculation(self, sfdi_stack:sd.SFDIStack) -> str:
        
        if sfdi_stack.axis_names == [sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y]:
            return "direct"
        
        elif sfdi_stack.axis_names == [sd.StackAxis.WAVELENGTH,sd.StackAxis.FREQUENCY, sd.StackAxis.X, sd.StackAxis.Y]:
            return "wavelength"
        
        else:
            raise ValueError("""Input SFDI stack has wrong format""".format(
                                    sfdi_stack.axis_names))
    
    def process(self, sfdi_stack:sd.SFDIStack, fit_mask:Optional[np.ndarray]=None) -> sd.SFDIStack:
        # Placeholder for reflectance fitting logic
        
        calculation_type = self._get_type_of_calculation(sfdi_stack)
        
        if fit_mask is None:
            fit_mask = np.ones(sfdi_stack.shape[-2:],dtype=np.bool_)
            
            
        if calculation_type == "direct":
                        
            fitted_data = self.reflectance_model.fit(sfdi_stack.spatial_frequencies,
                                                     sfdi_stack.data,fit_mask=fit_mask)
            results = np.array([fitted_data[par] for par in fitted_data.keys()])

            res = sd.SFDIStack(data=results, 
                            axis_names=[sd.StackAxis.RESULTS,sd.StackAxis.X,sd.StackAxis.Y],
                            parameter_names=list(fitted_data.keys()))

        elif calculation_type == "wavelength":
            
            _stack_iterator = sfdi_stack.iterate_over_axes(sd.StackAxis.WAVELENGTH)

            fit_data = []

            if sfdi_stack.wavelengths is None:
                raise ValueError("Input SFDI stack must have wavelengths defined for wavelength-based reflectance calculation.")
            for wv_id, stack_slice in _stack_iterator:
                
                wv_id = wv_id[0]
                wv = sfdi_stack.wavelengths[wv_id]
                
                fitted_data = self.reflectance_model.fit(sfdi_stack.spatial_frequencies,
                                                 stack_slice,fit_mask=fit_mask)
                
                results = np.array([fitted_data[par] for par in fitted_data.keys()])

                fit_data.append(results)
                
                
            res = sd.SFDIStack(data=np.array(fit_data),
                            axis_names=[sd.StackAxis.WAVELENGTH, sd.StackAxis.RESULTS,sd.StackAxis.X,sd.StackAxis.Y],
                            parameter_names=list(fitted_data.keys()), wavelengths=sfdi_stack.wavelengths)


        return res