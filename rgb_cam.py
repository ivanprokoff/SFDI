import cv2
from PIL import Image


class Camera():
    def __init__(self):
        self.cap = None
        self.width, self.height = 800,600
        self.open = False

    def open_camera(self):
        self.open = True
        self.release_camera()
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

        focus = 85  # min: 0, max: 255, increment:5
        # cap.set(3,1080)
        # cap.set(4,720)
        # cap.set(28, focus)
        self.cap.set(cv2.CAP_PROP_FOCUS, focus)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -0)
        self.get_frame()

    def get_frame(self):

        s, frame = self.cap.read()
        if s:  # frame captures without errors...
            img = Image.fromarray(frame[:, :, ::-1])

            return img



    def release_camera(self):
        #self.cap = False
       # print('cloooooose')
       # try:
        if self.cap:
            self.cap.release()

        # except AttributeError:


