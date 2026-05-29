import numpy as np
from IPython.display import HTML
import inspect

NOTEBOOK_DISPLAY_ENABLED = False

def disable_notebook_display():
    print("notebook display disabled")
    global NOTEBOOK_DISPLAY_ENABLED
    NOTEBOOK_DISPLAY_ENABLED = False


def enable_notebook_display():
    print("notebook display enabled")
    global NOTEBOOK_DISPLAY_ENABLED
    NOTEBOOK_DISPLAY_ENABLED = True

class NotebookDisplayMixin:
    """Mixin class for nice Jupyter notebook display"""
    
    def _repr_html_(self):
        """Generate HTML representation"""

        if not NOTEBOOK_DISPLAY_ENABLED:
            return None
        
        class_name = self.__class__.__name__
        
        # Get all non-private attributes
        attrs = {}
        for key, value in inspect.getmembers(self):
            if not key.startswith('_') and not callable(value):
                attrs[key] = value
        
        # Build HTML table
        html = f"""
        <div style="border: 1px solid #4CAF50; border-radius: 8px; padding: 12px; 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                    'Helvetica Neue', Arial, sans-serif;
                    background-color: #fafafa; margin: 5px 0;">
            <div style="color: #2c3e50; font-weight: 600; font-size: 1.1em; 
                        margin-bottom: 8px; border-bottom: 2px solid #4CAF50; 
                        padding-bottom: 4px;">
                {class_name}
            </div>
            <table style="width: 100%; font-size: 0.9em;">
        """
        
        # Display key attributes
        for key, value in attrs.items():
            if value is not None:
                # Format value nicely
                if isinstance(value, np.ndarray):
                    value_str = f"ndarray {value.shape}, {value.dtype}"
                elif isinstance(value, list) and len(value) > 5:
                    value_str = f"[{value[0]}, {value[1]}, ... {value[-1]}] ({len(value)} items)"
                elif isinstance(value, float):
                    value_str = f"{value:.4f}"
                else:
                    value_str = str(value)
                
                html += f"""
                    <tr style="border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 6px 8px; font-weight: 500; width: 35%; 
                                   color: #555;">
                            {key.replace('_', ' ').title()}:
                        </td>
                        <td style="padding: 6px 8px; color: #2c3e50; font-family: monospace;">
                            {value_str}
                        </td>
                    </tr>
                """
        
        html += """
            </table>
        </div>
        """
        return html
  