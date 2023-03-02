import cv2


class Camera():
    """Class for the rgb camera: closing, opening, frame acquisition"""

    def __init__(self, parent):
        self.cap = None
        self.width, self.height = 1920, 1080
        self.open = False

        self.open = True
        self.release_camera()
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

        self.cap.set(cv2.CAP_PROP_SETTINGS, 1)

    def open_camera(self):
        """Initiates the camera"""

        self.open = True
        self.release_camera()
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.get_frame()

    def get_frame(self):
        """Takes a photo and returns it"""
        s, frame = self.cap.read()
        if s:
            return frame[:, :-800]

    def release_camera(self):
        """Releases camera"""
        if self.cap:
            self.cap.release()


