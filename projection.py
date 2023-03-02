import customtkinter
from PIL import Image as I
from PIL import ImageEnhance
from pathlib import Path

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


def read_patterns_paths(colors=[
                                'red',
                               # 'green',
                               # 'blue'
],
                        freqs=[#'00',
                               '02',
                              # '04',
                               '06',
                              ## '08',
                               '10',
                               '12',
                             ##  '14',
                               '18',
                              # '22',
                               '26',
                               '32',
                               #'34',
                               '36',
                               '40',
                               '44',
                               '99'],
                        factors=[0.45, 0.6, 0.8],
                        patterns_folder='C:/Users/madpl/Documents/sfdi/projector'):
    """Reads paths to patterns for translation and saves them into a dictionary"""


    patterns_dict = {}
    for color, factor in zip(colors[:], factors):

        files = [str(i) for i in list((Path(f'{patterns_folder}/{color}/').glob('*')))]

        for file in files[:]:
            name = file.split('\\')[-1].split('.')[0]

            if name.split('_')[0] in freqs:
                patterns_dict[color, name] = (file, factor)
            name.split('_')[0]
    return patterns_dict


class Projection(customtkinter.CTkToplevel):
    """Class for the frame that projects patterens on the second window"""
    def __init__(self, parent):
        super().__init__()

        self.title("Projection")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.parent = parent
        # calculate position x and y coordinates
        x = 1950
        y = 0
        self.geometry('%dx%d+%d+%d' % (1900, 1200, x, y))

        self.pattern_window = customtkinter.CTkLabel(master=self, text='')

        self.pattern_window.grid(row=0, column=0, pady=[0, 0])
        self.white_image = I.new('RGB', (1920, 1080), (55,55, 55))
        self.tk_white_image = customtkinter.CTkImage(self.white_image, size=(1920, 1080))

        self.black_image = I.new('RGB', (1920, 1080), (0, 0, 0))
        self.tk_black_image = customtkinter.CTkImage(self.black_image, size=(1920, 1080))

    def set_first_picture(self):
        """Sets the first pattern image"""
        img_name = list(self.parent.patterns.values())[0]

        with I.open(img_name[0]) as im:

            enhancer = ImageEnhance.Brightness(im)

            # gives original image
            img = enhancer.enhance(img_name[1])

        tk_img = customtkinter.CTkImage(img, size=(1100, 1100))
        self.pattern_window.configure(image=tk_img)
        self.parent.pattern_copy.configure(tk_img)
        self.pattern_window.update()

        self.after(70)

    def set_background(self, color='black'):
        """Sets a black or white background to the projector window"""
        if color == 'black':
            self.pattern_window.configure(image=self.tk_black_image)

            self.pattern_window.update()

            self.after(50)
        else:
            self.pattern_window.configure(image=self.tk_white_image)

            self.pattern_window.update()

            self.after(50)


if __name__ == "__main__":
    app = Projection()
    print(app.patterns.keys())
    app.mainloop()
