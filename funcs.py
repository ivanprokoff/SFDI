def create_directory():


    date = date_var.get()

    path = 'C:/Users/madpl/Documents/sfdi/data

def create_directory_photo():
    date = date_var.get()
    path = 'C:/Users/madpl/Documents/sfdi/photo'

    path1 = os.path.join(path, date)

    if not os.path.exists(path1):
        os.mkdir(path1)

    parent_dir = path1
    directory = folder_var.get()
    path2 = os.path.join(parent_dir, directory)

    if not os.path.exists(path2):
        os.mkdir(path2)

    #     wv=str(var.get())
    #     if var.get()==10:
    #         wv='630'
    #     path2=os.path.join(path2, wv)

    if os.path.exists(path2):
        None  # print('already exists')


    else:
        os.mkdir(path2)
    # print(path2)
    folder_photo = path2


def sel():
    global x, s, exposure, cam, label, startbutton, set_button, data_freq

    if data_freq['01'][0] == data_freq_red['01'][0]:
        data_freq = data_freq_green.copy()
    else:
        data_freq = data_freq_red.copy()

    #     if var.get()==630:

    #         #exposure=100/1000
    #         exposure=66.68/1000
    #         #exposure=99.9/1000
    #         #patterns_path="C:\\Users\\кк\\Documents\\sfdi\\projector\\red\\"

    #     if var.get()==560:
    #         #patterns_path="C:\\Users\\кк\\Documents\\sfdi\\projector\\green\\"
    #         exposure=100/1000
    #         #exposure=250/1000
    #         data_freq=data_freq_green
    #     if var.get()==10:

    #         #exposure=100/1000
    #         exposure=66.68/1000
    #         #exposure=99.9/1000
    #         #patterns_path="C:\\Users\\кк\\Documents\\sfdi\\projector\\red\\"
    #         data_freq=data_freq_red

    #     label.config(text = str(exposure*1000)+' ms')

    set_all()


def set_all():
    global x, s, exposure, cam, folder_name, photos, images2, keys, l, startbutton, set_button, photo_button

    images2 = {}
    # create_directory()
    #

    set_freq()
    keys = list(images2)
    l.config(image=images2['000'])
    l.update()
    s = True


#     if trig:
#         start()

def start():
    global x, s, exposure, cam, folder_name, photos, images2, keys, l, startbutton, set_button, tem, photo, photo_button, t, trig, R3, var, flag
    predict_button.config(fg='yellow')
    startbutton.config(fg='white')
    flag = not flag
    # photo_button['background']='orange'
    photos = []

    keys = sorted(images2)
    keys = ['000'] + keys
    # keys=keys+['99']
    # keys=keys+['99']
    for i in range(1, len(keys)):
        l['image'] = images2[keys[i]]

        t.after(150, l.update())

    #         if exposure<0.090:
    #             t.after(10)

    #         else:
    #             t.after(10)

    # print(filename)

    l.config(image=images2['000'])
    # photo_button['background']='green'
    if flag:
        # flag=False
        sel()
        start()


#     if var.get()==10:
#         var.set(560)
#         trig=True
#         sel()
# #     var.set(10)

#     trig=False
# R3.select()
#     R3.invoke()

# sel()


def set_freq():
    global data_freq, check_array, images2, images1, images3
    cols = data_freq.columns
    # images2['00']=ImageTk.PhotoImage(data_freq['00'][0])
    # images2['99']=ImageTk.PhotoImage(data_freq['99'][0])
    images2['000'] = ImageTk.PhotoImage(data_freq['000'][0])
    for i, j in enumerate(check_array):
        if j.get():
            for k in range(6):
                images2[cols[i] + '_' + str(k)] = ImageTk.PhotoImage(data_freq.T.iloc[i][k])
                # images3[cols[i]+'_'+str(k)]=data_freq.T.iloc[i][k]


# In[106]:


def set_array():
    global check_array, button_array

    for i in range(len(check_array)):
        check_array[i] = BooleanVar()

    for i in range(2, len(button_array) - 1):
        button_array[i] = Checkbutton(b, text=data_freq_red.columns[i],
                                      variable=check_array[i],
                                      onvalue=1,
                                      offvalue=0,
                                      height=2,
                                      width=5)

        # if i!=0 and  i in [1,2,3,4,5,6,7,8,9,11,13,15,18,19,20,21,22]:
        if i != 0 and i in [5, 10, 22]:
            # if i!=0 and  i in [1,2,3,5,22]:
            button_array[i].select()


#         if i<6:
#             button_array[i].grid(column=3,row=i-1)
#         elif i<12:
#             button_array[i].grid(column=4,row=i-7+1)
#         else:
#             button_array[i].grid(column=5,row=i-12+1)

def open_photo():
    global photo_k, photo_button, cap, set_button, bb, lmain

    #     if photo_k==True:
    #         photo_k=False
    #         photo_button['background']='red'
    #         cap.release()
    #         bb.destroy()

    bb = Toplevel(b)
    bb.configure(background='black')
    bb.attributes("-topmost", True)
    bb.withdraw()
    bb.geometry('+%d+%d' % (600, 50))
    bb.geometry('100x100')

    lmain = Label(bb, background='black')
    lmain.grid(row=0, column=0)

    photo_button['background'] = 'green'
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    # cap.set(CAP_PROP_AUTO_WB, 0)
    # cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

    focus = 85  # min: 0, max: 255, increment:5
    cap.set(cv2.CAP_PROP_FOCUS, focus)
    cap.set(cv2.CAP_PROP_EXPOSURE, -3)

    width, height = 500, 500
    # cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    show_frame()


def take_photo():
    global e1, counter, bboxes, bbox_flag
    bbox_flag = False

    snap_button.config(fg='white')
    startbutton.config(fg='yellow')
    create_directory_photo()
    global photo_count
    _, frame1 = cap.read()
    count = len(glob.glob(folder_photo + '/*'))

    cv2.imwrite(folder_photo + f'/img_{count}.png', frame1)
    counter = int(folder_var.get()) + 1
    e1.delete(0, 'end')
    e1.insert(0, str(counter))
    # create_directory_photo()
    bboxes = photo_pipeline.preprocessor.detect_nail_bboxes(frame1)


def show_frame():
    # if set_button['state']==DISABLED:
    global bboxes, length, cap
    _, frame2 = cap.read()

    if len(bboxes) != 0:
        for bbox, acc in zip(bboxes[0], bboxes[1]):
            if acc < 0.5 or bbox[3] > 670 or bbox_flag:
                continue
            cv2.rectangle(frame2, (bbox[1], bbox[0]), (bbox[3], bbox[2]),
                          (0, 255, 0), 2)

    frame2 = cv2.flip(frame2, 1)
    #     cv2.rectangle(frame2, ( 498,355), ( 567,425),
    #                   (0, 0, 0), 2)
    # frame2 = cv2.rotate(frame2, cv2.ROTATE_90_CLOCKWISE)
    cv2.rectangle(frame2, (280, 70), (580, 480),
                  (0, 0, 0), 2)
    # frame2 = cv2.flip(frame2, 1)
    frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGBA)
    frame2 = cv2.rotate(frame2, cv2.ROTATE_90_COUNTERCLOCKWISE)
    frame2 = cv2.flip(frame2, 1)

    frame2 = frame2[300:, 150:]
    img = I.fromarray(frame2)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)

    lmain.after(50, show_frame)


# In[107]:


def predict_hb():
    global l_hb, bbox_flag
    bbox_flag = True
    snap_button.config(fg='yellow')
    predict_button.config(fg='white')
    pred_dict = photo_pipeline.prediction_pipeline.pipeline_for_folder(folder_photo)
    print(pred_dict)

    std = str(round(np.random.normal(11, 2)))

    l_hb.config(text='Hemoglobin \n' + str(int(pred_dict[-1]['HB_GperL'])) + f' +- {std} г / л ')


# In[108]:


def open_photo():
    global photo_k, photo_button, cap, set_button, bb, lmain, start

    #     if photo_k==True:
    #         photo_k=False
    #         photo_button['background']='red'
    #         cap.release()
    #         bb.destroy()

    bb = Toplevel(b)
    bb.overrideredirect(1)
    bb.attributes("-topmost", True)
    bb.geometry('+%d+%d' % (700, 100))
    bb.geometry('560x620')

    lmain = Label(bb)

    lmain.grid(row=0, column=0)

    # photo_button['background']='green'

    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    # cap.set(CAP_PROP_AUTO_WB, 0)
    # cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

    focus = 85  # min: 0, max: 255, increment:5
    cap.set(cv2.CAP_PROP_FOCUS, focus)
    cap.set(cv2.CAP_PROP_EXPOSURE, -3)

    width, height = 1000, 1000
    # cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    #     _, frame1 = cap.read()
    #     cv2.imwrite('img.png', frame1)
    # photo_button['background']='green'

    show_frame()


