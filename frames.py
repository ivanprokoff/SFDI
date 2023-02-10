import customtkinter
from open_close_button import Button
from PIL import Image as I
from external_functions import create_patient_directory


class Sidebar(customtkinter.CTkFrame):
    def __init__(self, parent, container):
        super().__init__(container)

        self.patient_entry = customtkinter.CTkEntry(self, justify='center')
        self.patient_entry.grid(row=0, column=0, padx=20, pady=10)
        self.patient_entry.insert(0, 'test')
        self.folder_button = customtkinter.CTkButton(self,
                                                     command=lambda *args: create_patient_directory(
                                                         self.patient_entry.get()),
                                                     text='Create directory')

        self.folder_button.grid(row=0, column=1, padx=10, pady=10)

        self.sidebar_button_1 = customtkinter.CTkButton(self,
                                                        command=lambda: [parent.camera.release_camera(),
                                                                         parent.image_change()],
                                                        text='Projection')

        self.sidebar_button_1.grid(row=1, column=1, padx=20, pady=10)

        self.rgb_button = Button(self)
        self.rgb_button.set_commands(open_text='open RGB camera', close_text='close RGB camera',
                                     open_commands=lambda *args: [self.rgb_button.change_function(),
                                                                  parent.camera.open_camera(),
                                                                  parent.translate_rgb_cam()],
                                     close_commands=lambda *args: [self.rgb_button.change_function(),
                                                                   parent.camera.release_camera()])
        self.rgb_button.grid(row=2, column=0, padx=20, pady=10)

        self.thor_button = Button(self)
        self.thor_button.set_commands(open_text='open Thor camera', close_text='close Thor camera',
                                      open_commands=lambda *args: [self.thor_button.change_function(),
                                                                   parent.thor_camera.open_camera()],
                                                                   #parent.translate_thor_cam()],
                                      close_commands=lambda *args: [self.thor_button.change_function(),
                                                                    parent.thor_camera.release_camera()])

        self.thor_button.grid(row=3, column=0, padx=20, pady=10)


class Translation(customtkinter.CTkFrame):
    def __init__(self, parent, container):
        super().__init__(container)

        self.pattern_copy = customtkinter.CTkLabel(self, image=None, text='')
        self.pattern_copy.grid(row=0, column=0, padx=2, pady=2)
        black_image = I.new('RGB', (700, 500))
        img = customtkinter.CTkImage(black_image, size=(800, 600))
        self.pattern_copy.configure(image=img)


class TabWindow(customtkinter.CTkTabview):
    def __init__(self, parent, container):
        super().__init__(container)

        self.add("Infrared")

        self.exposure_entry = customtkinter.CTkEntry(self.tab("Infrared"), justify='center')
        self.exposure_entry.insert(0, '100')

        self.exposure_entry.grid(row=0, column=0, columnspan=1, padx=(20, 20), pady=20, sticky="nsew")

        self.exposure_button = customtkinter.CTkButton(master=self.tab("Infrared"), fg_color="transparent",
                                                       text_color=("gray10", "#DCE4EE"), text='Set exposure',
                                                       border_width=1,
                                                       command=lambda: [parent.thor_camera.change_exposition(
                                                           int(self.exposure_entry.get()))])

        self.exposure_button.grid(row=1, column=0, padx=(20, 20), pady=(10, 10), sticky="nsew")

        self.infrared_name_entry = customtkinter.CTkEntry(self.tab("Infrared"), justify='center')
        self.infrared_name_entry.insert(0, '100')
        self.infrared_name_entry.grid(row=2, column=0, columnspan=1, padx=(20, 20), pady=20, sticky="nsew")

        self.thor_photo_button = customtkinter.CTkButton(master=self.tab("Infrared"), fg_color="transparent",
                                                         text_color=("gray10", "#DCE4EE"), text='Take photo',
                                                         border_width=1,
                                                         command=lambda *args: [
                                                             create_patient_directory(parent.patient_entry.get()),
                                                             parent.save_thor_image()])

        self.thor_photo_button.grid(row=3, column=0, padx=(20, 20), pady=(10, 10), sticky="nsew")

        self.add("Photo")

        self.add("SFDI")

        self.sfdi_button = customtkinter.CTkButton(master=self.tab("SFDI"), fg_color="transparent",
                                                   text_color=("gray10", "#DCE4EE"), text='SFDI',
                                                   command=lambda *arg: [create_patient_directory(parent.patient_entry.get()),
                                                                         parent.renew_current_directory(),
                                                                         parent.projection_window.set_first_picture(),


                                                                         parent.begin_sfdi()],
                                                   border_width=1)

        # self.tabview.tab("CTkTabview").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tab("SFDI").grid_columnconfigure(0, weight=1)
        self.sfdi_button.grid(row=1, column=0, padx=(20, 20), pady=(10, 10), sticky="nsew")
        # self.label_tab_2 = customtkinter.CTkLabel(self.tab("Tab 2"), text="CTkLabel on Tab 2")
        # self.label_tab_2.grid(row=0, column=0, padx=20, pady=20)
