import tkinter as tk
import tkinter.messagebox
import customtkinter
import numpy as np
from patterns_init import read_patterns
from PIL import ImageEnhance
import projection_func as pf
from PIL import Image as I
from open_close_button import Button
from projection import Projection
from rgb_cam import Camera
from thorcam import Thorcam

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


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
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets

        self.pattern_copy = customtkinter.CTkLabel(self, image=None,
                                                   # self.projection_window.pattern_window.cget("image"),
                                                   text='')

        self.pattern_copy.grid(row=0, column=1, padx=(20, 0), pady=(20, 0))
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="CustomTkinter",
                                                 font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_button_1 = customtkinter.CTkButton(master=self.sidebar_frame,
                                                        command=lambda: [self.camera.release_camera(),
                                                                         self.image_change()],
                                                        text='Projection')
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)

        # self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, command=lambda: [self.camera.open_camera(),
        #                                                                                      self.translate_rgb_cam()],
        #                                                 text='cam')
        # self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
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

        # self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, command=self.camera.release_camera,
        #                                                 text='close_camera')
        #
        # self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)

        # self.sidebar_button_4 = customtkinter.CTkButton(self.sidebar_frame,
        #                                                 command=lambda: [self.thor_camera.open_camera(),
        #                                                                  self.translate_thor_cam()],
        #                                                 text='thor_camera')
        #
        # self.sidebar_button_4.grid(row=4, column=0, padx=20, pady=10)
        #
        self.sidebar_button_5 = customtkinter.CTkButton(self.sidebar_frame, command=self.thor_camera.release_camera,
                                                        text='close_thor_camera')

        self.sidebar_button_5.grid(row=5, column=0, padx=20, pady=10)

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))

        self.entry = customtkinter.CTkEntry(self)
        self.entry.insert(0, '100')
        # self.entry.configure(textvariable='400')
        self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")

        self.main_button_1 = customtkinter.CTkButton(master=self, fg_color="transparent", border_width=2,
                                                     text_color=("gray10", "#DCE4EE"), text='Set exposure',
                                                     command=lambda: [print('change'),
                                                                      self.thor_camera.change_exposition(
                                                                          int(self.entry.get()))])
        self.main_button_1.grid(row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # create tabview
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=2, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.tabview.add("CTkTabview")
        self.tabview.add("Tab 2")
        self.tabview.add("Tab 3")
        self.tabview.tab("CTkTabview").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("Tab 2").grid_columnconfigure(0, weight=1)

        self.optionmenu_1 = customtkinter.CTkOptionMenu(self.tabview.tab("CTkTabview"), dynamic_resizing=False,
                                                        values=["Value 1", "Value 2", "Value Long Long Long"])
        self.optionmenu_1.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.combobox_1 = customtkinter.CTkComboBox(self.tabview.tab("CTkTabview"),
                                                    values=["Value 1", "Value 2", "Value Long....."])
        self.combobox_1.grid(row=1, column=0, padx=20, pady=(10, 10))
        self.string_input_button = customtkinter.CTkButton(self.tabview.tab("CTkTabview"), text="Open CTkInputDialog", )
        self.string_input_button.grid(row=2, column=0, padx=20, pady=(10, 10))
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
        # self.file = Button(self, text='Browse', command=self.choose)

        # create checkbox and switch frame
        # self.checkbox_slider_frame = customtkinter.CTkFrame(self)
        # self.checkbox_slider_frame.grid(row=1, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew")
        # self.checkbox_1 = customtkinter.CTkCheckBox(master=self.checkbox_slider_frame)
        # self.checkbox_1.grid(row=1, column=0, pady=(20, 10), padx=20, sticky="n")
        # self.checkbox_2 = customtkinter.CTkCheckBox(master=self.checkbox_slider_frame)
        # self.checkbox_2.grid(row=2, column=0, pady=10, padx=20, sticky="n")
        # self.switch_1 = customtkinter.CTkSwitch(master=self.checkbox_slider_frame,
        #                                         command=lambda: print("switch 1 toggle"))
        # self.switch_1.grid(row=3, column=0, pady=10, padx=20, sticky="n")
        # self.switch_2 = customtkinter.CTkSwitch(master=self.checkbox_slider_frame)
        # self.switch_2.grid(row=4, column=0, pady=(10, 20), padx=20, sticky="n")

        # create slider and progressbar frame
        # self.slider_progressbar_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        # self.slider_progressbar_frame.grid(row=1, column=1, columnspan=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        # self.slider_progressbar_frame.grid_columnconfigure(0, weight=1)
        # self.slider_progressbar_frame.grid_rowconfigure(4, weight=1)
        #
        # self.progressbar = customtkinter.CTkProgressBar(self.slider_progressbar_frame, mode='índeterminate',
        #                                                 indeterminate_speed=0.2)
        #
        # self.progressbar.grid(row=1, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        # self.progressbar.set(0)

        # set default values
        # self.sidebar_button_3.configure(state="disabled", text="Disabled CTkButton")
        #     self.checkbox_2.configure(state="disabled")
        #      self.switch_2.configure(state="disabled")
        #     self.checkbox_1.select()
        #     self.switch_1.select()
        #     self.radio_button_3.configure(state="disabled")

        # self.scaling_optionemenu.set("100%")
        self.optionmenu_1.set("CTkOptionmenu")
        self.combobox_1.set("CTkComboBox")
        # self.slider_1.configure()
        # self.slider_2.configure(command=self.progressbar_3.set)
        # self.progressbar_1.configure(mode="indeterminnate")
        # self.progressbar_1.start()
        # .insert("0.0", "CTkTextbox\n\n" + "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.\n\n" * 20)
        # self.seg_button_1.configure(values=["CTkSegmentedButton", "Value 2", "Value 3"])
        # self.seg_button_1.set("Value 2")

    def translate_rgb_cam(self):

        if self.thor_camera.open:
            self.thor_camera.release_camera()

        if self.camera.cap:
            raw_img = self.camera.get_frame()
            if raw_img is not None:
                img = customtkinter.CTkImage(raw_img, size=(500, 500))

                self.pattern_copy['image'] = img
                self.pattern_copy.configure(image=img)
                self.projection_window.pattern_window.after(10, self.translate_rgb_cam)

            else:
                black_image = I.new('RGB', (500, 500))
                img = customtkinter.CTkImage(black_image, size=(500, 500))
                self.pattern_copy.configure(image=img)

    def translate_thor_cam(self):

        # if self.thor_camera.cam:
        #     self.thor_camera.release_camera()
        if self.thor_camera.open:
            raw_img = self.thor_camera.get_frame()
            if raw_img is not None:
                img = I.fromarray(raw_img)
                img = customtkinter.CTkImage(img, size=(800, 1000))

                self.pattern_copy['image'] = img
                self.pattern_copy.configure(image=img)
                self.projection_window.pattern_window.after(15, self.translate_thor_cam)
        else:
            black_image = I.new('RGB', (500, 500))
            img = customtkinter.CTkImage(black_image, size=(500, 500))
            self.pattern_copy.configure(image=img)

    def image_change(self, clock=1, color='red'):
        self.sidebar_button_1.configure(text='pressed')
        freqs = list(self.projection_window.patterns[color].keys())
        # self.progressbar.set(0)
        print('value', self.entry.get())
        if clock < 5:
            i = clock
            with I.open(self.projection_window.patterns[color][freqs[i]][0]) as im:
                enhancer = ImageEnhance.Brightness(im)

                # gives original image
                img = enhancer.enhance(self.projection_window.patterns['red']['01_1'][1])
            img = customtkinter.CTkImage(img, size=(1000, 1000))

            self.projection_window.pattern_window['image'] = img
            self.projection_window.pattern_window['text'] = i
            self.projection_window.pattern_window.configure(image=img)
            self.pattern_copy.configure(image=img)

            clock += 1
            self.projection_window.pattern_window.after(10, self.image_change, clock)


if __name__ == "__main__":
    app = App()
    print('value', app.entry.get())
    app.mainloop()
