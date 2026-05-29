import numpy as np
from typing import List, Optional, Union
from dataclasses import dataclass,field
from enum import Enum
from sfdi_fitter.display import NotebookDisplayMixin

class StackAxis(Enum):
    FREQUENCY = 'frequency'
    PHASE = 'phase'
    X = 'x'
    Y = 'y'
    WAVELENGTH = 'wavelength'
    RESULTS = 'results'
    HEIGHT = 'height'
    SAMPLES = 'samples'


_axes_priority = {
    axis.name:i for i,axis in enumerate([StackAxis.HEIGHT,StackAxis.SAMPLES,StackAxis.WAVELENGTH,
    StackAxis.RESULTS,StackAxis.FREQUENCY,StackAxis.PHASE,StackAxis.X,StackAxis.Y])
}


@dataclass
class SFDIStack(NotebookDisplayMixin):

    data : np.ndarray
    axis_names : List[StackAxis]= field(default_factory=lambda :[StackAxis.FREQUENCY, StackAxis.PHASE, StackAxis.X, StackAxis.Y])
    spatial_frequencies: Optional[Union[List,np.ndarray]] = None
    parameter_names : Optional[List[str]] = None
    wavelengths : Optional[Union[List,np.ndarray]] = None

    _optional_fields = ['spatial_frequencies', 'parameter_names', 'wavelengths']
    
    def __repr__(self):
        repr_string = f"""SFDIStack(shape={self.data.shape}, dtype={self.data.dtype},\n 
        axis_names={self.axis_names}"""
        
        for _field_name in self._optional_fields:
            if getattr(self, _field_name) is not None:
                repr_string += f",\n {_field_name}={getattr(self, _field_name)}"
        repr_string += ")"
        return repr_string

    @property
    def shape(self):
        return self.data.shape
    
    @property
    def dtype(self):
        return self.data.dtype
        
    def get_axis_index(self, axis_name: StackAxis) -> int:
        """
        Get the index of the specified axis name.

        Args:
            axis_name (StackAxis): The axis enum value to retrieve the index for.

        Returns:
            int: The index of the specified axis name.

        Raises:
            ValueError: If the specified axis name is not found in the axis_names list.
        """
        if axis_name not in self.axis_names:
            raise ValueError(f"StackAxis name '{axis_name}' not found in axis_names.")
        return self.axis_names.index(axis_name)

    def reorder_axes(self, new_axis_order:List[StackAxis], inplace:bool=True) -> 'SFDIStack':
        """
        Reorder the axes of the data according to the specified new axis order.

        Args:
            new_axis_order (List[StackAxis]): The desired order of axes as a list of StackAxis enum values.
            inplace (bool): If True, modify the current instance. If False, return a new instance.

        Returns:
            SFDIStack: SFDIStack with the reordered data and updated axis names.    
        """
        if set(new_axis_order) != set(self.axis_names):
            raise ValueError("new_axis_order must contain the same StackAxis values as the current axis_names.")
        
        new_axis_indices = [self.get_axis_index(axis) for axis in new_axis_order]
        reordered_data = np.transpose(self.data, axes=new_axis_indices)

        if inplace:
            self.data = reordered_data
            self.axis_names = new_axis_order
            return self

        return SFDIStack(data=reordered_data, axis_names=new_axis_order, 
        spatial_frequencies=self.spatial_frequencies,
        parameter_names=self.parameter_names,      
        wavelengths=self.wavelengths)
        
    def get_noncoord_axes(self):
        """
        Get the non-coordinate axes of the SFDI stack.

        Returns:
            List[StackAxis]: A list of non-coordinate axes.
        """
        return [axis for axis in self.axis_names if not axis in [StackAxis.X, StackAxis.Y]]

    def iterate_over_axes(self, *axis_names:StackAxis):
        """
        Iterate over the specified axis names and yield the corresponding slices of the data.

        Args:
            axis_names (List[StackAxis]): A list of axis enum values to iterate over.
        Yields:
            Tuple[Tuple[int, ...], np.ndarray]: A tuple containing the indices of the current slice and the corresponding data slice.
        """
        axis_indices = [self.get_axis_index(axis_name) for axis_name in axis_names]
        for indices in np.ndindex(*[self.data.shape[i] for i in axis_indices]):
            slices = [slice(None)] * self.data.ndim
            for axis_index, index in zip(axis_indices, indices):
                slices[axis_index] = index
            yield indices, self.data[tuple(slices)]

    def get_standard_axis_order(self) -> List[StackAxis]:
        """
        Get the standard axis order for SFDI stacks.

        Returns:
            List[StackAxis]: The standard axis order as a list of StackAxis enum values.
        """
        return sorted(self.axis_names, key=lambda axis: _axes_priority[axis.name])
        
    def squeeze(self, axis_name:Optional[StackAxis]=None,inplace:bool=True) -> 'SFDIStack':
        """
        Squeeze the data along the specified axis name. If no axis name is provided, it will squeeze all axes with size 1.
        Args:
            axis_name (Optional[StackAxis]): The axis enum value to squeeze along. If None, all axes with size 1 will be squeezed.
            inplace (bool): If True, modify the current instance. If False, return a new instance.
        Returns:
            SFDIStack: SFDIStack with the squeezed data and updated axis names.
        """
        if axis_name is not None:
            axis_index = self.get_axis_index(axis_name)
            squeezed_data = np.squeeze(self.data, axis=axis_index)
            squeezed_axis_names = [name for i, name in enumerate(self.axis_names) if i != axis_index]
        else:
            squeezed_data = np.squeeze(self.data)
            squeezed_axis_names = [name for i, name in enumerate(self.axis_names) if self.data.shape[i] != 1]

        if inplace:
            self.data = squeezed_data
            self.axis_names = squeezed_axis_names   
            return self

        return SFDIStack(data=squeezed_data, axis_names=squeezed_axis_names, 
        spatial_frequencies=self.spatial_frequencies,
        parameter_names=self.parameter_names,
        wavelengths=self.wavelengths)
    
    def deep_copy(self) -> 'SFDIStack':
        """
        Creates a deep copy of this SFDIStack instance.

        Returns:
            SFDIStack: A deep copy of this instance.

        """
        from copy import deepcopy

        data_copy = np.copy(self.data)
        axis_names_copy = list(self.axis_names)

        spatial_frequencies_copy = None
        if self.spatial_frequencies is not None:
            if isinstance(self.spatial_frequencies, np.ndarray):
                spatial_frequencies_copy = np.copy(self.spatial_frequencies)
            else:
                spatial_frequencies_copy = deepcopy(self.spatial_frequencies)

        parameter_names_copy = None
        if self.parameter_names is not None:
            parameter_names_copy = list(self.parameter_names)

        wavelengths_copy = None
        if self.wavelengths is not None:
            if isinstance(self.wavelengths, np.ndarray):
                wavelengths_copy = np.copy(self.wavelengths)
            else:
                wavelengths_copy = deepcopy(self.wavelengths)

        return SFDIStack(
            data=data_copy,
            axis_names=axis_names_copy,
            spatial_frequencies=spatial_frequencies_copy,
            parameter_names=parameter_names_copy,
            wavelengths=wavelengths_copy
        )