from sfdi_fitter.demodulation import Processor
from sfdi_fitter.data import SFDIStack, StackAxis
from typing import Tuple, Union
from sfdi_fitter.display import NotebookDisplayMixin

class SFDIPipeline(Processor,NotebookDisplayMixin):
    """
    A class representing a processing pipeline for SFDI stacks. 
    It allows for sequential processing of SFDI stacks through a series of processors.

    Attributes:
        processors (list[Tuple[str, Processor]]): A list of tuples containing processor names and instances.    
    """
    def __init__(self, processors:list[Tuple[str,Processor]]):
        """
        Initialize the SFDIPipeline.

        Args:
            processors (list[Tuple[str,Processor]]): A list of tuples containing processor names and instances.
        """

        self.processors = processors
    
    def __repr__(self):
        processor_names = [ f'("{name}", {p.__repr__()}),\n' for name, p in self.processors[:-1]]
        processor_names.append(f'("{self.processors[-1][0]}", {self.processors[-1][1].__repr__()})')
        return f"SFDIPipeline(processors=[\n{''.join(processor_names)}])"
    
    def __getitem__(self, key:Union[int,slice]) -> list[Tuple[str, Processor]]:
        """
        Get a processor or a slice of processors from the pipeline.

        Args:
            key (Union[int, slice]): The index or slice of the processor(s) to retrieve.
        """
        if isinstance(key, int):
            return self.processors[key]
        elif isinstance(key, slice):
            return SFDIPipeline(self.processors[key])
        else:
            raise TypeError("Key must be an integer index or a slice.")

    def _get_step_kwargs(self, step_name:str, step_kwargs:dict) -> dict:
        """
        Get the keyword arguments for a specific processing step.

        Args:
            step_name (str): The name of the processing step to retrieve keyword arguments for.
            step_kwargs (dict): A dictionary containing the keyword arguments for the specified processing step.
        Returns:
            dict: A dictionary containing the keyword arguments for the specified processing step.
        """
        kwargs = {key: value for key, value in step_kwargs.items() if key.split("__")[0] == step_name}
        return kwargs

    def process(self, sfdi_stack:SFDIStack,**steps_kwargs) -> SFDIStack:
        """
        Process the input SFDI stack through the pipeline of processors.
        Args:
            sfdi_stack (SFDIStack): The input SFDI stack to be processed.
            **steps_kwargs: Keyword arguments for each processing step, where the key is in the format "processor_name__arg_name".

        Returns:
            SFDIStack: The processed SFDI stack after sequentially applying all processors in the pipeline.
        """
        if type(sfdi_stack) == SFDIStack:

            for processor_name,processor in self.processors:
                step_kwargs = self._get_step_kwargs(processor_name, steps_kwargs)
                sfdi_stack = processor.process(sfdi_stack,**step_kwargs)
            return sfdi_stack
        
        else:
            
            sfdi_stack_ = sfdi_stack.deep_copy()
            stack = sfdi_stack_.stack
            
            for processor_name,processor in self.processors:
                step_kwargs = self._get_step_kwargs(processor_name, steps_kwargs)
                stack = processor.process(stack,**step_kwargs)
            
            sfdi_stack_.stack = stack
            
            return sfdi_stack_