import pylablib as pll
from pylablib.devices import Thorlabs
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
            self.exposure = exposure / 1000
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

