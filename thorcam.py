import pylablib as pll
from pylablib.devices import Thorlabs
import customtkinter
pll.par["devices/dlls/thorlabs_tlcam"] = "path/to/dlls"


class Thorcam():
    def __init__(self, parent):
        self.cam = None

        self.open = False
        self.parent = parent

    def open_camera(self):
        self.release_camera()
        self.open = True

        self.cam = Thorlabs.ThorlabsTLCamera(serial='11354')

        self.cam.set_exposure(self.parent.exposure)
        self.cam.set_trigger_mode('int')



    def get_frame(self):
        self.cam.send_software_trigger()
        self.parent.projection_window.after(10)
        self.cam.wait_for_frame(since='lastread', nframes=1)
        img = self.cam.read_newest_image()

        return img

    def change_exposition(self, exposure):
        if self.cam is not None:
            self.cam.stop_acquisition()
            self.exposure = exposure / 1000
            self.cam.set_exposure(self.exposure)
            self.cam.start_acquisition(auto_start=False, nframes=1, frames_per_trigger=1)

    def release_camera(self):
        if self.cam:
            self.cam.close()
        self.open = False

    def stop_acquisition(self):
        if self.cam:
            self.cam.stop_acquisition()

