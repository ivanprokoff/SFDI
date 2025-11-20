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

    def check_frame_quality(self, frame, max_val=1023, over_thresh=1000, under_thresh=200, over_percent_limit=5,
                            under_percent_limit=90):
        """
        Проверяет кадр на засветы и недоэкспозицию.
        Возвращает: (is_good: bool, message: str)
        """

        if frame is None:
            return False, "No frame captured"

        flat = frame.flatten().astype(float)
        mean_int = np.mean(flat)
        over_count = np.sum(flat > over_thresh) / len(flat) * 100
        under_count = np.sum(flat < under_thresh) / len(flat) * 100

        if over_count > over_percent_limit:
            return False, f"Overexposure: {over_count:.1f}% pixels > {over_thresh}"
        if under_count > under_percent_limit:
            return False, f"Underexposure: {under_count:.1f}% pixels < {under_thresh}, mean={mean_int:.1f}"
        if mean_int < 300 or mean_int > 900:
            return False, f"Bad mean intensity: {mean_int:.1f} (should be 300-900)"

        return True, "Frame quality OK"