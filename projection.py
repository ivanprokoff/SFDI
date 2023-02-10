import tkinter as tk
import tkinter.messagebox
import customtkinter
import numpy as np
from PIL import Image as I
from PIL import ImageEnhance
from pathlib import Path
import projection_func as pf

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


def read_patterns_paths(colors=['red', 'green', 'blue'], factors=[0.2, 0.2, 0.2],
                  patterns_folder='C:/Users/madpl/Documents/sfdi/projector/'):
    '''
    reads patterns to a dictionary
    '''

    patterns_dict = {}
    for color, factor in zip(colors[:1], factors):

        files = [str(i) for i in list((Path(f'{patterns_folder}/{color}/').glob('*')))]


        for file in files[20:44]:
            name = file.split('\\')[-1].split('.')[0]
            # with I.open(file) as im:
            #     enhancer = ImageEnhance.Brightness(im)

                # gives original image
                #im_output = enhancer.enhance(factor)
            patterns_dict[color, name] = (file, factor)
    return patterns_dict


class Projection(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__()

        self.title("Projection")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.parent = parent
        # calculate position x and y coordinates
        x = 1800
        y = 0#(screen_height / 2) - (screen_height / 2)
        #self.geometry('%dx%d+%d+%d' % (screen_width, screen_height, x, y))
        self.state('zoomed')
        self.geometry('%dx%d+%d+%d' % (1400, 1700, x, y))
        # with I.open(self.patterns['red', '01_1'][0]) as im:
        #     enhancer = ImageEnhance.Brightness(im)
        #
        #     # gives original image
        #     img = enhancer.enhance(self.patterns['red', '01_1'][1])
        #
        # tk_img = customtkinter.CTkImage(img)
        self.pattern_window = customtkinter.CTkLabel(master=self, text='')

        self.pattern_window.grid(row=0, column=1)

    def set_first_picture(self):
        img_name = list(self.parent.patterns.values())[0]
        with I.open(img_name[0]) as im:
            enhancer = ImageEnhance.Brightness(im)

                # gives original image
            img = enhancer.enhance(img_name[1])

        tk_img = customtkinter.CTkImage(img)
        self.pattern_window.configure(image=tk_img)

if __name__ == "__main__":

    app = Projection()
    print(app.patterns.keys())
    app.mainloop()
