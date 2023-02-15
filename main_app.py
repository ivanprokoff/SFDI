import tkinter as tk
import cv2
import customtkinter
import numpy as np
import os.path
import sys
import time
import external_functions
from PIL import ImageEnhance
import projection_func as pf
from PIL import Image as I
from open_close_button import Button
from projection import Projection, read_patterns_paths
from rgb_cam import Camera
from thorcam import Thorcam
from frames import Sidebar, Translation, TabWindow, Log_Window

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.animation = True
        self.bind('<Escape>', lambda *args: [self.animation_stop(), sys.exit(1)])
        self.flag = True
        self.first_frame = True
        self.current_directory = None
        self.title("Clinical app")
        self.patterns = read_patterns_paths()
        self.iter_patterns = iter(self.patterns)
        self.exposure = 66.68 / 1000
        self.geometry('%dx%d+%d+%d' % (1520, 700, 0, 0))
        self.camera = Camera()
        self.thor_camera = Thorcam(self)

        """
        SIDEBAR FRAME
        """
        container = customtkinter.CTkFrame(self, width=80, height=1, corner_radius=0, border_width=1, border_color='white')


        container.grid(row=0, column=0, rowspan=1, columnspan=1, pady=[50,10], padx=20,sticky = 'NW')

        self.sidebar_frame = Sidebar(self, container)
        self.patient_entry = self.sidebar_frame.patient_entry
        self.sidebar_frame.grid(row=0, column=0)

        """
          Log_frame
        """
        container = customtkinter.CTkFrame(self, width=40, height=1, corner_radius=0)
        container.grid(row=1, column=2, rowspan=1, columnspan=1, pady=[10, 10], padx=20, sticky='nswe')

        self.log_frame = Log_Window(self, container)
        self.text_box = self.log_frame.textbox
        self.log_frame.grid(row=0, column=0)

        """
        Central frame
        """
        container_center = customtkinter.CTkFrame(self, width=90, height=100, border_color='white', border_width=1)
        container_center.grid(row=0, column=4, rowspan=5, columnspan=1, pady=50, padx=20, sticky="NW")

        self.translation_frame = Translation(self, container_center)
        self.translation_frame.grid(row=0, column=0, rowspan=10)
        self.pattern_copy = self.translation_frame.pattern_copy

        """
        TAB frame
        """
        self.tab_frame = customtkinter.CTkFrame(self, width=30, height=1, corner_radius=0, border_width=1,
                                                border_color='white')
        self.tab_frame.grid(row=0, column=2, padx=10, pady=(40, 0), columnspan=1, sticky="NW")

        container = customtkinter.CTkTabview(self.tab_frame, width=40, height=10)
        container.grid(row=0, column=0, padx=20, pady=(0, 0), sticky="NseW")

        self.tabview = TabWindow(self, container)
        self.tabview.grid(row=0, column=0,columnspan=2)

        self.projection_window = Projection(self)
        # self.projection_window.set_first_picture()
        self.infrared_name_entry = self.tabview.infrared_name_entry

    def insert_log(self, command='Infrared', *args):

        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        if command == 'SFDI':
            line = f'{current_time}     {self.patient_entry.get()} SFDI measured'
            self.text_box.insert('0.0', line+'\n')

        if command == 'Infrared':

           # line = f'{current_time}      {self.infrared_name_entry.get()} Photo_taken'
            line = f'{current_time}      {args}'
            self.text_box.insert('0.0', line+'\n')
        if command == 'RGB':

            line = f'{current_time}      {args}'
            self.text_box.insert('0.0', line+'\n')
        if command == 'Directory':
            line = f'{current_time}      {self.patient_entry.get()} directory created'
            self.text_box.insert('0.0', line + '\n')
        if command == 'Predict':
            line = f'{current_time}      {self.patient_entry.get()} {args}'
            self.text_box.insert('0.0', line + '\n')





    def translate_rgb_cam(self):

        self.flag = True
        while self.animation and self.flag and self.camera.cap:

            frame = self.camera.get_frame()

            frame = cv2.flip(frame, 1)
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            frame = cv2.flip(frame, 0)
            frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            frame = frame[:, :, ::-1]

            pil_img = I.fromarray(frame)

            if frame is not None:
                img = customtkinter.CTkImage(pil_img, size = (np.shape(pil_img)[1],np.shape(pil_img)[0]))

                self.pattern_copy['image'] = img
                self.pattern_copy.configure(image=img)
                self.pattern_copy.update()

            else:
                black_image = I.new('RGB', (500, 500))
                img = customtkinter.CTkImage(black_image, size=(500,500))
                self.pattern_copy.configure(image=img)
            self.after(15)

    def renew_current_directory(self):
        self.current_directory = external_functions.return_current_directory(self.patient_entry.get())

    def save_thor_image(self, filename=''):
        if self.thor_camera.open:
            self.renew_current_directory()
            img = self.thor_camera.get_frame()
            filename = f'{self.current_directory}/Infrared/{self.tabview.infrared_name_entry.get()}_{self.tabview.exposure_entry.get()}_1.TIF'

            for i in range(1, 10):

                if os.path.isfile(filename):
                    filename = filename[:-5]
                    filename += f'{i}.TIF'
                else:
                    I.fromarray(img).save(filename)
                    self.insert_log('Infrared', filename[38:])

                    break

    def save_rgb_image(self, filename=''):
        if self.camera.cap:
            self.renew_current_directory()
            img = self.camera.get_frame()
            filename = f'{self.current_directory}/Photo/1.png'

            for i in range(1, 10):

                if os.path.isfile(filename):
                    filename = filename[:-5]
                    filename += f'{i}.png'
                else:
                    cv2.imwrite(filename, img)
                    self.insert_log('RGB', filename[38:])

                    break

    def translate_thor_cam(self):

        self.flag = True
        while self.flag and self.thor_camera.open:
            raw_img = self.thor_camera.get_frame()
            if raw_img is not None:
                raw_img = raw_img.astype('float')[::2,::2].T
                thor_img = I.fromarray(raw_img * 255 // 1023)

                tk_thor_img = customtkinter.CTkImage(thor_img, size = (np.shape(raw_img)[1],
                                                                                np.shape(raw_img)[0]
                                                                                )

                                                     )

                self.pattern_copy.configure(image=tk_thor_img)

                self.pattern_copy.update()

            else:
                print('else')
                black_image = I.new('RGB', (500, 500))
                img = customtkinter.CTkImage(black_image, size=(500, 500))
                self.pattern_copy.configure(image=img)
            self.after(30)

    def image_change(self, clock=1, color='blue'):
        # self.sidebar_button_1.configure(text='pressed')
        for i in range(5):
            try:
                img_name = self.patterns[next(self.iter_patterns)]
                with I.open(img_name[0]) as im:
                    enhancer = ImageEnhance.Brightness(im)

                    # gives original image
                    img = enhancer.enhance(0.5)

                tk_img = customtkinter.CTkImage(img, size=(800, 600))
                # self.pattern_copy['image'] = tk_img
                self.pattern_copy.configure(image=tk_img)

                tk_img = customtkinter.CTkImage(img, size=(1200, 900))
                # self.projection_window.pattern_window['image'] = tk_img
                self.projection_window.pattern_window.configure(image=tk_img)

                self.projection_window.update()



            except StopIteration:
                self.create_iter_patterns()
                self.first_frame = False

    def stop(self):
        self.thor_camera.stop_acquisition()
        self.camera.release_camera()
        self.flag = False

    def begin_sfdi(self):

        self.thor_camera.cam.set_exposure(self.exposure)
        self.thor_camera.cam.start_acquisition(auto_start=False, nframes=1, frames_per_trigger=1)
        pattern_list = list(self.patterns.items())
        pattern_list = pattern_list+[pattern_list[-1]]
        self.after(40)
        self.flag = True

        for i, (key, img_name) in enumerate(pattern_list[:]):
            if not self.flag:
                break
            with I.open(img_name[0]) as im:
                enhancer = ImageEnhance.Brightness(im)
                # gives original image
                img = enhancer.enhance(img_name[1])

            img = customtkinter.CTkImage(img, size=(np.shape(img)[1], np.shape(img)[0]))

            self.projection_window.pattern_window['image'] = img
            self.projection_window.pattern_window.configure(image=img)
            self.projection_window.update()

            self.after(40)

            raw_img = self.thor_camera.get_frame().T
            translation_img = raw_img.astype('float')[::2, ::2]*255//1023
            if raw_img is not None:
                thor_img = I.fromarray(raw_img)

                tk_thor_img = customtkinter.CTkImage(I.fromarray(translation_img), size=(np.shape(translation_img)[1],
                                                                                np.shape(translation_img)[0]))

                file_name = f'{self.current_directory}/SFDI/{pattern_list[i-1][0][0]}/{pattern_list[i-1][0][1]}.TIF'

                while os.path.isfile(file_name):
                    self.patient_entry.insert('end', '_1')
                    external_functions.create_patient_directory(self.patient_entry.get())
                    self.renew_current_directory()
                    file_name = f'{self.current_directory}/SFDI/{pattern_list[i - 1][0][0]}/{pattern_list[i - 1][0][1]}.TIF'

                if i != 0:
                    thor_img.save(file_name)


                self.pattern_copy.configure(image=tk_thor_img)

                self.pattern_copy.update()
        self.insert_log('SFDI')
        self.thor_camera.cam.stop_acquisition()


    def animation_stop(self):

        self.animation = False


if __name__ == "__main__":
    external_functions.create_today_directory()
    app = App()
    app.mainloop()
