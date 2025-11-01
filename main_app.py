import cv2
import customtkinter

import numpy as np
import os.path
import sys
import external_functions
from PIL import ImageEnhance, ImageDraw
from PIL import Image as I
from projection import Projection, read_patterns_paths
from rgb_cam import Camera
from thorcam import Thorcam
from frames import Side_Frame, Translation, TabWindow, Log_Window
import time

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

PATTERN_COORDS_TO_SAVE = (150,850,150,650) #bot,top,left,right or "upper","lower", left, right in PIL notation

def save_sfdi_image(thor_img, file_name, save_only_pattern_part=False,
                    pattern_coords=None):
    """
    Save image from camera. If save_only_pattern_part is True,
    save only part that has "projection" on it using coordinates passed through pattern_coords tuple

    :param thor_img: (PIL.Image) Image from Thorlabs Camer
    :param file_name: (str) Path to file
    :param save_only_pattern_part: (bool) - default False
    :param pattern_coords: tuple(int) - bot,top,left,right
    :return: None
    """

    if save_only_pattern_part:
        assert not pattern_coords is None, "Pattern coordinates should be specified! is save_only_pattern is True"
        # row-column notation. Upper-lower - first coord,
        # upper should be less than lower
        # left-right - second coord. left should be less than right

        upper,lower,left,right = pattern_coords
        sub_image = thor_img.crop((left, upper, right, lower))
        sub_image.save(file_name)
    else:
        thor_img.save(file_name)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.animation = True
        self.bind('<Escape>', lambda *args: [sys.exit(1)])
        self.flag = True
        self.first_frame = True
        self.current_directory = None
        self.title("Clinical app")
        self.patterns = read_patterns_paths()
        self.iter_patterns = iter(self.patterns)
        self.preloaded_patterns = {}
        for key, (path, factor) in self.patterns.items():
            with I.open(path) as im:
                enhancer = ImageEnhance.Brightness(im)
                enhanced_img = enhancer.enhance(factor)
                ctk_img = customtkinter.CTkImage(enhanced_img, size=(enhanced_img.width, enhanced_img.height))
                self.preloaded_patterns[key] = ctk_img

        self.exposure = 66.68 / 1000  # МЕНЯЛИ ДЛЯ УСТРАННЕНИЯ РАССИНХРОНА
        self.geometry('%dx%d+%d+%d' % (1520, 700, 0, 0))

        self.camera = Camera(self)
        self.thor_camera = Thorcam(self)

        """
        SIDEBAR FRAME
        """
        container = customtkinter.CTkFrame(self, width=80, height=1, corner_radius=0, border_width=1,
                                           border_color='RED')
        container.grid(row=0, column=0, rowspan=1, columnspan=1, pady=[50, 10], padx=20, sticky='NW')

        self.sidebar_frame = Side_Frame(self, container)
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
        Frame window for camera translation
        """
        container_center = customtkinter.CTkFrame(self, width=90, height=100, border_color='black', border_width=1)
        container_center.grid(row=0, column=4, rowspan=5, columnspan=1, pady=50, padx=20, sticky="NW")

        self.translation_frame = Translation(self, container_center)
        self.translation_frame.grid(row=0, column=0, rowspan=10)
        self.pattern_copy = self.translation_frame.pattern_copy

        """
        TAB frame with all methods
        """
        self.tab_frame = customtkinter.CTkFrame(self, width=30, height=1, corner_radius=0, border_width=1,
                                                border_color='black')
        self.tab_frame.grid(row=0, column=2, padx=10, pady=(40, 0), columnspan=1, sticky="NW")

        container = customtkinter.CTkTabview(self.tab_frame, width=40, height=10)
        container.grid(row=0, column=0, padx=20, pady=(0, 0), sticky="NseW")

        self.tabview = TabWindow(self, container)
        self.tabview.grid(row=0, column=0, columnspan=2)

        self.projection_window = Projection(self)

        # self.projection_window.set_first_picture()
        self.infrared_name_entry = self.tabview.infrared_name_entry

    def translate_rgb_cam(self):
        """Translates view from rgb cam"""
        self.flag = True
        while self.animation and self.flag and self.camera.cap:

            frame = self.camera.get_frame()
            if frame is not None:
                frame = cv2.flip(frame, 1)
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                frame = cv2.flip(frame, 0)
                frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

                frame = frame[:, :, ::-1]

                pil_img = I.fromarray(frame)
                img = customtkinter.CTkImage(pil_img, size=(np.shape(pil_img)[1], np.shape(pil_img)[0]))

                draw = ImageDraw.Draw(pil_img)

                draw.rectangle(((133, 320), (177, 350)), fill=None, outline=255)

                draw.rectangle(((233, 238), (267, 272)), fill=None, outline=255)
                draw.rectangle(((313, 285), (347, 310)), fill=None, outline=255)

                # draw.rectangle(((570 // 2, 570 // 2), (510 // 2, 490 // 2)), fill=None, outline=255)


                self.pattern_copy['image'] = img
                self.pattern_copy.configure(image=img)
                self.pattern_copy.update()

            else:
                black_image = I.new('RGB', (500, 500))
                img = customtkinter.CTkImage(black_image, size=(500, 500))
                self.pattern_copy.configure(image=img)
            self.after(5)

    def renew_current_directory(self, mode='SFDI'):
        """Updates current directory variable"""
        self.current_directory = external_functions.return_current_directory(self.patient_entry.get(), mode)

    def save_thor_image(self, filename=''):
        """Saves an image from thorcam during infrared measurements """
        if self.thor_camera.open:
            self.renew_current_directory('Infrared')
            img = self.thor_camera.get_frame()
            filename = f'{self.current_directory}/{self.tabview.infrared_name_entry.get()}_{self.tabview.exposure_entry.get()}_1.TIF'

            for i in range(1, 10):

                if os.path.isfile(filename):
                    filename = filename[:-5]
                    filename += f'{i}.TIF'
                else:
                    I.fromarray(img).save(filename)
                    self.log_frame.insert_log('Infrared', filename[38:])

                    break

    def save_rgb_image(self, filename=''):
        """Saves rgb cam image during Photo mode"""
        if self.camera.cap:
            self.renew_current_directory(mode='Photo')
            img = self.camera.get_frame()
            filename = f'{self.current_directory}/1.png'

            for i in range(1, 10):

                if os.path.isfile(filename):
                    filename = filename[:-5]
                    filename += f'{i}.png'
                else:
                    cv2.imwrite(filename, img)
                    self.log_frame.insert_log('RGB', filename[38:])

                    break

    def translate_thor_cam(self):
        """Translates thorcam view"""
        self.flag = True
        while self.flag and self.thor_camera.cam is not None and self.thor_camera.open:
            raw_img = self.thor_camera.get_frame()
            if raw_img is not None:
                raw_img = (raw_img.astype('float')[::2, ::2].T * 255 // 1023).astype('uint8')

                thor_img = I.fromarray(raw_img).transpose(I.FLIP_LEFT_RIGHT)
                draw = ImageDraw.Draw(thor_img)
                draw.rectangle(((625 // 2, 1080 // 2), (380 // 2, 850 // 2)), fill=None, outline=255)

                draw = ImageDraw.Draw(thor_img)
                draw.rectangle(((570 // 2, 570 // 2), (510 // 2, 490 // 2)), fill=None, outline=255)

                tk_thor_img = customtkinter.CTkImage(thor_img, size=(np.shape(raw_img)[1],
                                                                     np.shape(raw_img)[0]
                                                                     )

                                                     )

                self.pattern_copy.configure(image=tk_thor_img)

                self.pattern_copy.update()

            else:

                black_image = I.new('RGB', (500, 500))
                img = customtkinter.CTkImage(black_image, size=(500, 500))
                self.pattern_copy.configure(image=img)
            self.after(30)

    def stop(self):
        """Stops cameras and pattern translation"""
        self.thor_camera.stop_acquisition()
        self.camera.release_camera()
        self.flag = False
        external_functions.change_button_state(self, block=False)

    def begin_sfdi(self):
        """A loop for pattern translation to projector, taking thorcam photos and
        saving them in a relevant directory. Rather large function for now."""
        blue_flag = True
        green_flag = True
        red_flag = True
        time_multiplication_factor = 1.0
        save_only_pattern_part = True
        red_exposure_time = 66.68 * 3 # МЕНЯЛИ ДЛЯ УСТРАННЕНИЯ РАССИНХРОНА

        if self.thor_camera.cam:
            self.thor_camera.cam.set_exposure(self.exposure)

            self.thor_camera.cam.start_acquisition(auto_start=False, nframes=1, frames_per_trigger=1)
            pattern_list = list(self.patterns.items())
            pattern_list = pattern_list + [pattern_list[-1]]
            self.flag = True
            external_functions.change_button_state(self, block=True)

        else:
            self.log_frame.insert_log('Exception')
            return

        for i, (key, img_name) in enumerate(pattern_list[:]):
            if not self.flag:
                self.projection_window.set_background()
                break
            with I.open(img_name[0]) as im:

                enhancer = ImageEnhance.Brightness(im)
                img = enhancer.enhance(img_name[1])
            img = customtkinter.CTkImage(img, size=(np.shape(img)[1], np.shape(img)[0]))

            self.projection_window.pattern_window['image'] = img
            self.projection_window.pattern_window.configure(image=img)
            self.projection_window.update()
            self.after(int(time_multiplication_factor*30))

            raw_img = self.thor_camera.get_frame()

            if raw_img is not None:
                translation_img = (raw_img.T.astype('float')[::2, ::2] * 255 // 1023).astype('uint8')
                translation_img = I.fromarray(translation_img).transpose(I.FLIP_LEFT_RIGHT)

                draw = ImageDraw.Draw(translation_img)
                draw.rectangle(((570//2, 570//2), (510//2, 490//2)), fill=None, outline=255)

                thor_img = I.fromarray(raw_img)
                tk_thor_img = customtkinter.CTkImage(translation_img, size=(np.shape(translation_img)[1],
                                                                            np.shape(translation_img)[0]))

                file_name = f'{self.current_directory}/{pattern_list[i - 1][0][0]}/{pattern_list[i - 1][0][1]}.TIF'

                if os.path.isfile(file_name):
                    self.patient_entry.configure(state='normal')
                    while os.path.isfile(file_name):
                        self.patient_entry.insert('end', '_1')
                        external_functions.create_patient_directory(self.patient_entry.get(), modes=['SFDI'])
                        self.renew_current_directory('SFDI')
                        file_name = f'{self.current_directory}/{pattern_list[i - 1][0][0]}/{pattern_list[i - 1][0][1]}.TIF'
                    self.patient_entry.configure(state='disabled')

                if i != 0:
                    save_sfdi_image(thor_img, file_name,
                                    save_only_pattern_part=save_only_pattern_part,
                                    pattern_coords=PATTERN_COORDS_TO_SAVE)


                self.pattern_copy.configure(image=tk_thor_img)
                self.pattern_copy.update()
                self.after(int(time_multiplication_factor*15))


            if red_flag and 'red' in img_name[0]:
                self.thor_camera.change_exposition(red_exposure_time)
                red_flag = False
            self.after(int(time_multiplication_factor*20))


            # if red_flag and ' red' in img_name[0]:
            #     self.thor_camera.change_exposition(100)
            #     red_flag = False



        self.log_frame.insert_log('SFDI')
       # self.after(2000)
        #self.thor_camera.cam.stop_acquisition()
        #self.after(2000)
        external_functions.change_button_state(self, block=False)
        self.after(2000)


if __name__ == "__main__":
    external_functions.create_today_directory()
    app = App()
    app.mainloop()
