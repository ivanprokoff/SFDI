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
from frames import Sidebar, Translation, TabWindow
customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Clinical app")

        self.geometry('%dx%d+%d+%d' % (1520, 800, 0, 0))
        self.camera = Camera()
        self.thor_camera = Thorcam()

        self.projection_window = Projection()

        """
        SIDEBAR FRAME
        """
        container = customtkinter.CTkFrame(self, width=80, height=100, corner_radius=0)
        container.grid(row=0, column=0, rowspan=4, columnspan=2, pady=50, padx=10, sticky="nsew")

        self.sidebar_frame = Sidebar(self, container)
        self.sidebar_frame.grid(row=0, column=0)



        """
        Central frame
        """
        container_center = customtkinter.CTkFrame(self, width=90, height=100, border_color='white', border_width=1)
        container_center.grid(row=0, column=3, rowspan=1, pady=50, padx=10, columnspan=1, sticky="nsew")

        self.translation_frame = Translation(self, container_center)
        self.translation_frame.grid(row=0, column=0)
        self.pattern_copy = self.translation_frame.pattern_copy


        """
        TAB frame
        """

        container = customtkinter.CTkTabview(self, width=200)
        container.grid(row=0, column=2, padx=10, pady=(50, 0), sticky="nsew")

        self.tabview = TabWindow(self, container)
        self.tabview.grid(row=0, column=0)


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
            filename = f'{self.tabview.infrared_name_entry.get()}_{self.tabview.exposure_entry.get()}.TIF'
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
       # self.sidebar_button_1.configure(text='pressed')
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
