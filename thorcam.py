import pylablib as pll
from pylablib.devices import Thorlabs

pll.par["devices/dlls/thorlabs_tlcam"] = "path/to/dlls"


class Thorcam():
    def __init__(self, exposure=200 /1000):
        self.cam = None
        self.open = False
        #self.width, self.height = 800, 600
        #self.open = False
        self.exposure = exposure

    def open_camera(self):
        self.release_camera()
        self.open = True
        self.cam = Thorlabs.ThorlabsTLCamera(serial='11354')

        self.cam.set_exposure(self.exposure)
        self.cam.set_trigger_mode('int')
        self.cam.start_acquisition(auto_start=False, nframes=1, frames_per_trigger=1)


    def get_frame(self):

        self.cam.send_software_trigger()
        self.cam.wait_for_frame(since='lastwait', nframes=1)
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

