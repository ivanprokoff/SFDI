import cv2
import customtkinter

import numpy as np
import os.path
import sys
import external_functions
from PIL import ImageEnhance, ImageDraw, ImageFont
from PIL import Image as I
from projection import Projection, read_patterns_paths
from rgb_cam import Camera
from thorcam import Thorcam
from frames import Side_Frame, Translation, TabWindow, Log_Window
import time
import tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


try:
    # Попробуем загрузить шрифт с поддержкой кириллицы
    font = ImageFont.truetype("arial.ttf", 28)
except:
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except:
        font = ImageFont.load_default()  # fallback

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

PATTERN_COORDS_TO_SAVE = (100,900,0,800) #bot,top,left,right or "upper","lower", left, right in PIL notation

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
        self.color_exposures_ms = {
            'green': 40.68,
            'blue': 66.68,
            'red': 66.68
        }
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
        """Обновлённый поток камеры с безопасной отрисовкой ROI и текста"""
        self.flag = True
        while self.flag and self.thor_camera.cam is not None and self.thor_camera.open:
            raw_img = self.thor_camera.get_frame()
            if raw_img is not None:
                # Масштабируем 2x (как у тебя было)
                display_img = (raw_img.astype('float')[::2, ::2].T * 255 // 1023).astype('uint8')
                display_img = I.fromarray(display_img).transpose(I.FLIP_LEFT_RIGHT)
                draw = ImageDraw.Draw(display_img)

                # Рисуем ROI и текст ТОЛЬКО во время проверки качества
                if getattr(self, 'show_roi_overlay', False):
                    left, top, right, bottom = self.quality_roi
                    scale = 0.5
                    rect_coords = [
                        (left * scale, top * scale),
                        (right * scale, bottom * scale)
                    ]
                    draw.rectangle(rect_coords, outline="yellow", width=4)

                    # Текст на английском (чтобы не падало) или используем безопасный шрифт
                    color_en = getattr(self, 'current_roi_color', 'unknown').capitalize()
                    text = f"Check: {color_en}"

                    # Безопасная отрисовка текста
                    try:
                        draw.text((12, 8), text, fill="yellow", font=font)
                        draw.text((10, 10), text, fill="black", font=font)  # обводка
                    except:
                        # Если совсем ничего не работает — рисуем без текста
                        pass

                tk_img = customtkinter.CTkImage(display_img, size=(display_img.width, display_img.height))
                self.pattern_copy.configure(image=tk_img)
                self.pattern_copy.update()

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
        self.check_quality()
        if tkinter.messagebox.askyesno("Proceed?", "Quality check done. Proceed with SFDI?"):
            for i, (key, img_name) in enumerate(pattern_list[:]):
                if not self.flag:
                    self.projection_window.set_background()
                    break
                color = key[0]
                exp_ms = self.color_exposures_ms.get(color, 66.68)
                self.thor_camera.change_exposition(exp_ms)
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


                # if red_flag and 'red' in img_name[0]:
                #    self.thor_camera.change_exposition(red_exposure_time)
                #    red_flag = False
                # self.after(int(time_multiplication_factor*20))


                # if red_flag and ' red' in img_name[0]:
                #     self.thor_camera.change_exposition(100)
                #     red_flag = False
        else:
            return


        self.log_frame.insert_log('SFDI')
       # self.after(2000)
        #self.thor_camera.cam.stop_acquisition()
        #self.after(2000)
        external_functions.change_button_state(self, block=False)
        self.after(2000)

    def _create_solid_color_image(self, color_rgb, size=(1920, 1080)):
        """Создаёт сплошное изображение заданного цвета"""
        img = I.new('RGB', size, color_rgb)
        return customtkinter.CTkImage(img, size=size)

    def _get_solid_patterns(self):
        """Возвращает словарь с заливками для каждого цвета"""
        return {
            'green': self._create_solid_color_image((0, 255, 0)),
            'blue': self._create_solid_color_image((0, 0, 255)),
            'red': self._create_solid_color_image((255, 0, 0)),
        }

    def check_quality(self):
        """Запуск проверки качества с последовательной сменой цветов"""
        if not self.thor_camera.cam or not self.thor_camera.open:
            tkinter.messagebox.showerror("Ошибка", "Thorlabs камера не открыта!")
            return

        self.tabview.quality_check_button.configure(state="disabled", text="Проверка...")

        self.quality_check_results = []
        self.quality_check_colors = ['red', 'green', 'blue']
        self.quality_check_index = 0
        self.quality_roi = (150, 150, 650, 850)  # left, top, right, bottom
        self.show_roi_overlay = True

        # Сплошные заливки
        self.solid_images = {
            'red': self._create_solid_color_image((255, 0, 0)),
            'green': self._create_solid_color_image((0, 255, 0)),
            'blue': self._create_solid_color_image((0, 0, 255)),
        }

        self.log_frame.insert_log('Quality Check', 'Запуск проверки качества...')
        self._quality_check_step()

    def _quality_check_step(self):
        """Один шаг: проецирует цвет -> ждёт -> снимает -> следующий"""
        if self.quality_check_index >= len(self.quality_check_colors):
            self.show_roi_overlay = False
            self._quality_check_finish()
            return

        color = self.quality_check_colors[self.quality_check_index]
        self.current_roi_color = color

        # Устанавливаем экспозицию и проецируем
        self.thor_camera.change_exposition(self.color_exposures_ms[color])
        self.projection_window.pattern_window.configure(image=self.solid_images[color])
        self.projection_window.update_idletasks()
        self.projection_window.update()

        # Даём проектору 1400 мс на полную стабилизацию
        self.after(1400, self._capture_and_analyze, color)

    def _capture_and_analyze(self, color):
        """Снимает кадр, анализирует, сохраняет результат"""
        raw_img = self.thor_camera.get_frame()
        is_good = False
        msg = "Кадр не получен"

        if raw_img is not None:
            l, t, r, b = self.quality_roi
            roi = raw_img[t:b, l:r]
            mean_val = roi.mean()
            over = np.sum(roi > 950) / roi.size * 100
            under = np.sum(roi < 100) / roi.size * 100

            is_good = over < 3.0 and 180 < mean_val < 880
            msg = f"OK (ср. {mean_val:.0f})" if is_good else f"Проблема: пересвет {over:.1f}% / ср. {mean_val:.0f}"

            if not hasattr(self, 'final_quality_frames'):
                self.final_quality_frames = {}
            self.final_quality_frames[color] = roi

        self.quality_check_results.append((color, is_good, msg))
        self.log_frame.insert_log('Quality Check', f"{color.capitalize()}: {msg}")

        self.quality_check_index += 1
        self._quality_check_step()

    def _quality_check_finish(self):
        self.projection_window.set_background('black')
        self.show_roi_overlay = False

        result_window = customtkinter.CTkToplevel(self)
        result_window.title("Результаты проверки качества проекции")
        result_window.geometry("1400x800")
        result_window.transient(self)
        result_window.grab_set()

        customtkinter.CTkLabel(
            result_window,
            text="Проверка качества проекции (ROI)",
            font=("Arial", 24, "bold")
        ).pack(pady=(15, 10))

        fig = Figure(figsize=(13, 5), dpi=110)
        canvas = FigureCanvasTkAgg(fig, result_window)
        canvas.get_tk_widget().pack(padx=30, pady=10, fill="both", expand=True)

        gs = fig.add_gridspec(1, 3, hspace=0.15, wspace=0.25)

        metrics = []

        for idx, color in enumerate(['red', 'green', 'blue']):
            ax = fig.add_subplot(gs[0, idx])
            roi = self.final_quality_frames.get(color)

            if roi is not None:
                mean_val = roi.mean()
                over = np.sum(roi > 950) / roi.size * 100
                under = np.sum(roi < 100) / roi.size * 100
                std_val = roi.std()

                im = ax.imshow(roi, cmap='hot', vmin=0, vmax=1023)
                ax.set_title(color.capitalize(), fontsize=18, fontweight='bold', color=color, pad=20)
                ax.axis('off')
                fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.8)

                status = "OK" if (over < 3.0 and 180 < mean_val < 880) else "ПРОБЛЕМА"

                metrics.append({
                    'color': color.capitalize(),
                    'mean': mean_val,
                    'over': over,
                    'under': under,
                    'std': std_val,
                    'status': status
                })
            else:
                ax.text(0.5, 0.5, "НЕТ ДАННЫХ", transform=ax.transAxes,
                        ha='center', va='center', color='white', fontsize=20, weight='bold',
                        bbox=dict(boxstyle="round", facecolor="red", alpha=0.8))
                ax.axis('off')
                metrics.append({'color': color.capitalize(), 'status': "ОШИБКА"})

        canvas.draw()

        table_frame = customtkinter.CTkFrame(result_window)
        table_frame.pack(pady=15, padx=60, fill="x")

        headers = "Канал    │   Среднее   │ Пересвет % │ Недосвет % │ Разброс │   Статус"
        customtkinter.CTkLabel(
            table_frame,
            text=headers,
            font=("Consolas", 14, "bold"),
            fg_color="#2b2b2b", corner_radius=8, padx=10, pady=8
        ).pack(pady=5)

        all_good = True
        for m in metrics:
            if m['status'] != 'OK':
                all_good = False

            color_fg = "#00ff00" if m['status'] == 'OK' else "#ff4444"
            line = (f"{m['color']:6} │ "
                    f"{m['mean']:8.0f} │ "
                    f"{m['over']:7.1f} │ "
                    f"{m['under']:7.1f} │ "
                    f"{m['std']:6.0f} │ "
                    f"{m['status']:8}")

            customtkinter.CTkLabel(
                table_frame,
                text=line,
                font=("Consolas", 13),
                text_color=color_fg,
                padx=10, pady=4
            ).pack()

        verdict_text = "ГОТОВО К SFDI!" if all_good else "ТРЕБУЕТСЯ КОРРЕКЦИЯ ЭКСПОЗИЦИИ"
        verdict_color = "#00ff00" if all_good else "#ff4444"

        customtkinter.CTkLabel(
            result_window,
            text=verdict_text,
            font=("Arial", 22, "bold"),
            text_color=verdict_color
        ).pack(pady=20)

        customtkinter.CTkButton(
            result_window,
            text="Закрыть",
            width=200, height=40,
            command=result_window.destroy
        ).pack(pady=10)

        if hasattr(self, 'final_quality_frames'):
            del self.final_quality_frames

        self.tabview.quality_check_button.configure(state="normal", text="Проверить качество")


if __name__ == "__main__":
    external_functions.create_today_directory()
    app = App()
    app.mainloop()
