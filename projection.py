import tkinter as tk
import tkinter.messagebox
import customtkinter
import numpy as np
from patterns_init import read_patterns
from PIL import ImageTk
import projection_func as pf

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class Projection(customtkinter.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.patterns = read_patterns()
        self.title("CustomTkinter complex_example.py")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # calculate position x and y coordinates
        x = 1500
        y = (screen_height / 2) - (screen_height / 2)
        #self.geometry('%dx%d+%d+%d' % (screen_width, screen_height, x, y))
        #self.state('zoomed')
        self.geometry(f"{500}x{500}")
        img = self.patterns['red']['01_1']
        tk_img = customtkinter.CTkImage(img, size=(500, 500))
        self.pattern_window = customtkinter.CTkLabel(master=self, image=tk_img, text='')

        self.pattern_window.grid(row=0, column=1, padx=(20, 0), pady=(20, 0))


if __name__ == "__main__":
    app = Projection()
    app.mainloop()
