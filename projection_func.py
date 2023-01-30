import tkinter as tk
from PIL import ImageTk


def set_array(check_array, button_array, data_freq_red, images, base):
    for i in range(len(check_array)):
        check_array[i] = tk.BooleanVar()

    for i in range(2, len(button_array) - 1):

        button_array[i] = tk.Checkbutton(base, text=data_freq_red.columns[i],
                                         variable=check_array[i],
                                         onvalue=1,
                                         offvalue=0,
                                         height=2,
                                         width=5)

        # if i!=0 and  i in [1,2,3,4,5,6,7,8,9,11,13,15,18,19,20,21,22]:
        if i != 0 and i in [5, 10, 22]:

            button_array[i].select()
    return button_array


def sel(data_freq, data_freq_red, data_freq_green):
    if data_freq['01'][0] == data_freq_red['01'][0]:
        data_freq = data_freq_green.copy()
    else:
        data_freq = data_freq_red.copy()

    set_all()


def set_all(pattern_window):
    images = {}

    set_freq()
    keys = list(images)
    pattern_window.config(image=images['000'])
    pattern_window.update()


def start(start_button, images, main_window, pattern_window, flag):
    start_button.config(fg='white')
    photos = []

    keys = sorted(images)
    keys = ['000'] + keys
    for i in range(1, len(keys)):
        pattern_window['image'] = images[keys[i]]
        main_window.after(150, pattern_window.update())

    pattern_window.config(image=images['000'])

    if flag:
        # flag=False
        sel()
        start()


def set_freq(data_freq, images, check_array):

    cols = data_freq.columns
    images['000'] = ImageTk.PhotoImage(data_freq['000'][0])
    for i, j in enumerate(check_array):
        # or j.get()
        if True:
            for k in range(6):
                images[cols[i] + '_' + str(k)] = ImageTk.PhotoImage(data_freq.T.iloc[i][k])

    return images
