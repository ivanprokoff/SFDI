import pylablib as pll
from pylablib.devices import Thorlabs
import numpy as np
pll.par["devices/dlls/thorlabs_tlcam"] = "path/to/dlls"


class Thorcam():
    """Class for dealing with Thorlabs camera: opening, closing, taking images"""
    def __init__(self, parent):
        self.cam = None

        self.open = False
        self.parent = parent

    def open_camera(self):
        """Initiates the camera"""
        self.release_camera()
        self.open = True

        self.cam = Thorlabs.ThorlabsTLCamera(serial='11354')

        self.cam.set_exposure(self.parent.exposure)
        self.cam.set_trigger_mode('int')

    def get_frame(self):
        """Reads the last frame"""
        self.cam.send_software_trigger()
        self.parent.projection_window.after(15)
        self.cam.wait_for_frame(since='lastread', nframes=1)
        img = self.cam.read_newest_image()

        return img

    def change_exposition(self, exposure):
        """Changes exposition of the camera"""
        if self.cam is not None:
            self.cam.stop_acquisition()
            self.exposure = exposure/3000
            self.cam.set_exposure(self.exposure)
            self.cam.start_acquisition(auto_start=False, nframes=1, frames_per_trigger=1)

    def release_camera(self):
        """Releases camera"""
        if self.cam:
            self.cam.close()
        self.open = False

    def stop_acquisition(self):
        """Stops camera acquisition"""
        if self.cam:
            self.cam.stop_acquisition()

    def check_frame_quality(self, frame, over_thresh=950, over_percent_limit=3.0,
                            under_thresh=100, under_percent_limit=80,
                            min_mean=150, max_mean=850):
        """Расширенная проверка кадра ТОЛЬКО в ROI"""
        if frame is None:
            return False, "Кадр не получен"

        flat = frame.flatten().astype(np.float32)
        total_pixels = len(flat)
        mean_val = np.mean(flat)

        overexposed_pixels = np.sum(flat > over_thresh)
        underexposed_pixels = np.sum(flat < under_thresh)

        over_percent = overexposed_pixels / total_pixels * 100
        under_percent = underexposed_pixels / total_pixels * 100

        if over_percent > over_percent_limit:
            return False, f"Переэкспозиция: {over_percent:.1f}% > {over_thresh}"
        if under_percent > under_percent_limit:
            return False, f"Недоэкспозиция: {under_percent:.1f}% < {under_thresh}, среднее={mean_val:.0f}"
        if mean_val < min_mean:
            return False, f"Слишком тёмно: среднее={mean_val:.0f} < {min_mean}"
        if mean_val > max_mean:
            return False, f"Слишком ярко: среднее={mean_val:.0f} > {max_mean}"

        return True, f"OK (среднее={mean_val:.0f}, переэксп: {over_percent:.1f}%)"