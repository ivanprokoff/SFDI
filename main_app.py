import tkinter as tk
import tkinter.messagebox
import customtkinter
import numpy as np
import external_functions
from PIL import ImageEnhance
import projection_func as pf
from PIL import Image as I
from open_close_button import Button
from projection import Projection
from rgb_cam import Camera
from thorcam import Thorcam

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("CustomTkinter complex_example.py")
        # self.geometry(f"{1500}x{800}")
        self.geometry('%dx%d+%d+%d' % (1500, 800, 0, 0))

        self.camera = Camera()
        self.thor_camera = Thorcam()

        self.projection_window = Projection()
        # configure grid layout (4x4)
        # self.grid_columnconfigure(1, weight=1)
        # self.grid_columnconfigure((2, 3), weight=0)
        # self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets



        self.sidebar_frame = customtkinter.CTkFrame(self, width=100,height=100, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, pady=50, padx=20, sticky="nsew")
        #self.sidebar_frame.grid_rowconfigure(4, weight=1)



        self.central_frame = customtkinter.CTkFrame(self, width=90, height=100, border_color='white', border_width=1)

        self.central_frame.grid(row=0, column=1, rowspan=2, pady=50, columnspan=1, sticky="nsew")
        #self.central_frame.grid_rowconfigure(1, weight=1)

        self.pattern_copy = customtkinter.CTkLabel(self.central_frame, image=None,
                                                   # self.projection_window.pattern_window.cget("image"),
                                                   text='')

        self.pattern_copy.grid(row=0, column=0, padx=2, pady=2)
        black_image = I.new('RGB', (800, 600))
        img = customtkinter.CTkImage(black_image, size=(800, 600))
        self.pattern_copy.configure(image=img)

        self.sidebar_button_1 = customtkinter.CTkButton(master=self.sidebar_frame,
                                                        command=lambda: [self.camera.release_camera(),
                                                                         self.image_change()],
                                                        text='Projection')

        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)


        self.rgb_button = Button(self.sidebar_frame)
        self.rgb_button.set_commands(open_text='open RGB camera', close_text='close RGB camera',
                                     open_commands=lambda *args: [self.rgb_button.change_function(),
                                                                  self.camera.open_camera(),
                                                                  self.translate_rgb_cam()],
                                     close_commands=lambda *args: [self.rgb_button.change_function(),
                                                                   self.camera.release_camera()])
        self.rgb_button.grid(row=2, column=0, padx=20, pady=10)

        self.thor_button = Button(self.sidebar_frame)
        self.thor_button.set_commands(open_text='open Thor camera', close_text='close Thor camera',
                                      open_commands=lambda *args: [self.thor_button.change_function(),
                                                                   self.thor_camera.open_camera(),
                                                                   self.translate_thor_cam()],
                                      close_commands=lambda *args: [self.thor_button.change_function(),
                                                                    self.thor_camera.release_camera()])

        self.thor_button.grid(row=3, column=0, padx=20, pady=10)



        # create tabview
        self.tabview = customtkinter.CTkTabview(self, width=200)
        self.tabview.add("Infrared")
        self.tabview.grid(row=0, column=2, padx=(20, 0), pady=(50, 0), sticky="nsew")
        self.exposure_entry = customtkinter.CTkEntry(self.tabview.tab("Infrared"))
        self.exposure_entry.insert(0, '100')

        self.exposure_entry.grid(row=0, column=0, columnspan=1, padx=(20, 20), pady=20, sticky="nsew")

        self.exposure_button = customtkinter.CTkButton(master=self.tabview.tab("Infrared"), fg_color="transparent",
                                                       text_color=("gray10", "#DCE4EE"), text='Set exposure', border_width=1,
                                                       command=lambda: [
                                                                        self.thor_camera.change_exposition(
                                                                            int(self.exposure_entry.get()))])

        self.exposure_button.grid(row=1, column=0, padx=(20, 20), pady=(10, 10), sticky="nsew")

        self.infrared_name_entry = customtkinter.CTkEntry(self.tabview.tab("Infrared"))
        self.infrared_name_entry.insert(0, '100')
        self.infrared_name_entry.grid(row=2, column=0, columnspan=1, padx=(20, 20), pady=20, sticky="nsew")

        self.thor_photo_button = customtkinter.CTkButton(master=self.tabview.tab("Infrared"), fg_color="transparent",
                                                       text_color=("gray10", "#DCE4EE"), text='Take photo', border_width=1,
                                                       command=lambda: [self.save_thor_image()])

        self.thor_photo_button.grid(row=3, column=0, padx=(20, 20), pady=(10, 10), sticky="nsew")





        self.tabview.add("Tab 2")
        self.tabview.add("Tab 3")
        #self.tabview.tab("CTkTabview").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("Tab 2").grid_columnconfigure(0, weight=1)




        self.label_tab_2 = customtkinter.CTkLabel(self.tabview.tab("Tab 2"), text="CTkLabel on Tab 2")
        self.label_tab_2.grid(row=0, column=0, padx=20, pady=20)

        # create radiobutton frame
        self.radiobutton_frame = customtkinter.CTkFrame(self)
        self.radiobutton_frame.grid(row=0, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.radio_var = tkinter.IntVar(value=0)
        self.label_radio_group = customtkinter.CTkLabel(master=self.radiobutton_frame, text="CTkRadioButton Group:")
        self.label_radio_group.grid(row=0, column=2, columnspan=1, padx=10, pady=10, sticky="")
        self.radio_button_1 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           value=0)
        self.radio_button_1.grid(row=1, column=2, pady=10, padx=20, sticky="n")
        self.radio_button_2 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           value=1)
        self.radio_button_2.grid(row=2, column=2, pady=10, padx=20, sticky="n")
        self.radio_button_3 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           value=2)
        self.radio_button_3.grid(row=3, column=2, pady=10, padx=20, sticky="n")


    def translate_rgb_cam(self):

        if self.thor_camera.open:
            self.thor_camera.release_camera()

        if self.camera.cap:
            raw_img = self.camera.get_frame()
            if raw_img is not None:
                img = customtkinter.CTkImage(raw_img, size=(800, 600))

                self.pattern_copy['image'] = img
                self.pattern_copy.configure(image=img)
                self.projection_window.pattern_window.after(10, self.translate_rgb_cam)

            else:
                black_image = I.new('RGB', (800, 600))
                img = customtkinter.CTkImage(black_image, size=(800, 600))
                self.pattern_copy.configure(image=img)

    def save_thor_image(self, filename=''):
        if self.thor_camera.open:
            img = self.thor_camera.get_frame()
            filename = f'{self.infrared_name_entry.get()}_{self.exposure_entry.get()}.TIF'
            I.fromarray(img).save(filename)

    def translate_thor_cam(self):

        # if self.thor_camera.cam:
        #     self.thor_camera.release_camera()
        if self.thor_camera.open:
            raw_img = self.thor_camera.get_frame()
            if raw_img is not None:
                img = I.fromarray(raw_img)
                img = customtkinter.CTkImage(img, size=(800, 600))

                self.pattern_copy['image'] = img
                self.pattern_copy.configure(image=img)
                self.projection_window.pattern_window.after(15, self.translate_thor_cam)
        else:
            black_image = I.new('RGB', (800, 800))
            img = customtkinter.CTkImage(black_image, size=(800, 600))
            self.pattern_copy.configure(image=img)

    def image_change(self, clock=1, color='red'):
        self.sidebar_button_1.configure(text='pressed')
        freqs = list(self.projection_window.patterns[color].keys())
        if clock < 10:
            i = clock
            with I.open(self.projection_window.patterns[color][freqs[i]][0]) as im:
                enhancer = ImageEnhance.Brightness(im)

                # gives original image
                img = enhancer.enhance(self.projection_window.patterns['red']['01_1'][1])
            img = customtkinter.CTkImage(img, size=(800, 600))

            self.projection_window.pattern_window['image'] = img
            self.projection_window.pattern_window['text'] = i
            self.projection_window.pattern_window.configure(image=img)
            self.pattern_copy.configure(image=img)

            clock += 1
            self.projection_window.pattern_window.after(10, self.image_change, clock)


if __name__ == "__main__":
    external_functions.create_today_directory()
    app = App()
    app.mainloop()
