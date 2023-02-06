import pylablib as pll
from pylablib.devices import Thorlabs

pll.par["devices/dlls/thorlabs_tlcam"] = "path/to/dlls"


class Thorcam():
    def __init__(self, exposure=100 / 1000):
        self.cam = None
        self.width, self.height = 800, 600
        self.open = False
        self.exposure = exposure

    def open_camera(self):
        self.release_camera()
        self.cam = Thorlabs.ThorlabsTLCamera(serial='11354')

        self.cam.set_exposure(self.exposure)
        self.cam.set_trigger_mode('int')
        self.cam.start_acquisition(auto_start=False, nframes=1, frames_per_trigger=1)

    def get_frame(self):

        self.cam.send_software_trigger()
        self.cam.wait_for_frame(since='lastwait', nframes=1)
        img = self.cam.read_newest_image()

        return img

    def release_camera(self):
        if self.cam:
            self.cam.close()


if __name__ == "__main__":
    app = Thorcam()
    app.open_camera()