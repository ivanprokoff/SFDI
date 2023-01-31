import tkinter as tk
import tkinter.messagebox
import customtkinter
import numpy as np
from patterns_init import pics
from PIL import ImageTk
import projection_func as pf

data_freq_red, data_freq_green = pics()

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

freqs = data_freq_red.columns

check_array = list(np.zeros(len(freqs)))
button_array = list(np.zeros(len(freqs)))
images = {}


# images = pf.set_freq(data_freq_red, images, check_array)


class Projection(customtkinter.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("CustomTkinter complex_example.py")
        self.geometry(f"{500}x{500}")

        # configure grid layout (4x4)
        # self.grid_columnconfigure(1, weight=1)
        # self.grid_columnconfigure((2, 3), weight=0)
        # self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        # self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        # self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        # self.sidebar_frame.grid_rowconfigure(4, weight=1)
        # # self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="CustomTkinter",
        # #                                          font=customtkinter.CTkFont(size=20, weight="bold"))
        # # self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        # self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, command=self.image_change)
        # self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        # # configure window

        # main_window = tk.Toplevel(self.sidebar_frame)
        img = customtkinter.CTkImage(data_freq_red['000'][0], size=(500, 500))
        self.pattern_window = customtkinter.CTkLabel(master=self, image=img, text='')

        self.pattern_window.grid(row=0, column=1, padx=(20, 0), pady=(20, 0))
        self.cols = data_freq_red.columns

    def image_change(self, clock=1, data_freq_red=data_freq_red):
        cols = data_freq_red.columns


        if clock < 5:
            i = clock
            img = customtkinter.CTkImage(data_freq_red[cols[3]].iloc[i], size=(500, 500))

            self.pattern_window['image'] = img
            self.pattern_window['text'] = i
            self.pattern_window.configure(image=img, text=i)
            clock += 1
            self.pattern_window.after(100, self.image_change,clock)

if __name__ == "__main__":
    app =  Projection()
    app.mainloop()



