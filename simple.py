import cv2
from tkinter import *
from PIL import Image, ImageTk

cam_on = False
cap = None
mainWindow = Tk()

mainFrame = Frame(mainWindow, height=640, width=810)
mainFrame.place(x=350, y=0)

cameraFrame = Frame(mainWindow, height=640, width=405)
cameraFrame.place(x=0, y=0)


def show_frame():
    if cam_on:

        ret, frame = cap.read()

        if ret:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image).resize((810, 640))
            imgtk = ImageTk.PhotoImage(image=img)
            vid_lbl.imgtk = imgtk
            vid_lbl.configure(image=imgtk)

        vid_lbl.after(10, show_frame)


def start_vid():
    global cam_on, cap
    stop_vid()
    cam_on = True
    cap = cv2.VideoCapture(0)
    show_frame()


def stop_vid():
    global cam_on
    cam_on = False

    if cap:
        cap.release()


vid_lbl = Label(mainFrame)
vid_lbl.grid(row=0, column=0)

# Buttons
TurnCameraOn = Button(cameraFrame, text="start Video", bg="blue", command=start_vid)
TurnCameraOn.place(x=0, y=0)
TurnCameraOff = Button(cameraFrame, text="stop Video", bg="blue", command=stop_vid)
TurnCameraOff.place(x=0, y=300)

mainWindow.mainloop()