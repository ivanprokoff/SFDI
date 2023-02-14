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


def read_patterns_paths(colors=['red', 'green', 'blue'],
                        freqs=['00','01','02','04','12','16','20','32', '40','44'],
                        factors=[0.3, 0.5, 0.5],
                  patterns_folder='C:/Users/madpl/Documents/sfdi/projector/'):
    '''
    reads patterns to a dictionary
    '''

    patterns_dict = {}
    for color, factor in zip(colors[:], factors):

        files = [str(i) for i in list((Path(f'{patterns_folder}/{color}/').glob('*')))]


        for file in files[:]:
            name = file.split('\\')[-1].split('.')[0]
            # with I.open(file) as im:
            #     enhancer = ImageEnhance.Brightness(im)
            if name.split('_')[0] in freqs:
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
        x = 2000
        y = 0
        self.geometry('%dx%d+%d+%d' % (1500, 1700, x, y))
        self.pattern_window = customtkinter.CTkLabel(master=self, text='')

        self.pattern_window.grid(row=0, column=1)


    def set_first_picture(self):
        img_name = list(self.parent.patterns.values())[0]

        with I.open(img_name[0]) as im:
            enhancer = ImageEnhance.Brightness(im)

                # gives original image
            img = enhancer.enhance(img_name[1])

        tk_img = customtkinter.CTkImage(img, size=(1200, 900))
        self.pattern_window.configure(image=tk_img)
        self.parent.pattern_copy.configure(tk_img)
        self.pattern_window.update()

        self.after(50)


if __name__ == "__main__":

    app = Projection()
    print(app.patterns.keys())
    app.mainloop()
