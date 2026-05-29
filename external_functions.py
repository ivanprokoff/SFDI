from datetime import datetime
import os
import numpy as np


#import photo_pipeline_2


def create_today_directory(main_path='C:/Users/madpl/clinic_data'):
    """Creates directories for the current day"""
    date = str(datetime.date(datetime.now()))

    for mode in ['SFDI', 'Photo', 'Infrared', 'Logs']:
        date_path = f'{main_path}/{mode}/{date}'
        os.makedirs(date_path, exist_ok=True)

    log_path = f'{main_path}/Logs/{date}/{date}_log.txt'

    if not os.path.isfile(log_path):
        with open(log_path, 'w') as f:
            f.write('')


def create_patient_directory(patient_id, modes=['SFDI', 'Infrared', 'Photo'], main_path='C:/Users/madpl/clinic_data'):
    """Creates directories for the current patient/phantom"""
    date = str(datetime.date(datetime.now()))

    for method in modes:
        folder_id = f'{main_path}/{method}/{date}/{patient_id}'

        if patient_id:
            os.makedirs(folder_id, exist_ok=True)

        if patient_id and method == 'SFDI':
            for color in ['red', 'green', 'blue']:

                folder_name = f'{main_path}/SFDI/{date}/{patient_id}/{color}'
                os.makedirs(folder_name, exist_ok=True)


def return_current_directory(patient_id, mode='SFDI', main_path='C:/Users/madpl/clinic_data'):
    """Returns the current directory depending on the entry fields"""
    date = str(datetime.date(datetime.now()))
    return f'{main_path}/{mode}/{date}/{patient_id}'


def predict_hb(parent):
    """Class docstrings go here."""
    1
    # parent.renew_current_directory(mode='Photo')
    #
    # folder_photo = f'{parent.current_directory}'
    #
    # pred_dict = photo_pipeline_2.prediction_pipeline.pipeline_for_folder(folder_photo)
    # print(folder_photo)
    # print(pred_dict)
    #args = 'Hb level='+str(int(pred_dict[-1]['HB_GperL']))+'g/L'
    random_prediction = np.random.randint(120, 140)
    args = 'Hb level=' + str(int(random_prediction)) + ' g/L'
    print(args)
    parent.insert_log('Predict', args)


def change_button_state(parent, block=True):
    """Disables and enables buttons for a safe sfdi measurement"""

    if block:
        parent.patient_entry.configure(state='disabled')
        parent.sidebar_frame.folder_button.configure(state='disabled')
        parent.sidebar_frame.white_button.configure(state='disabled')
        parent.sidebar_frame.black_button.configure(state='disabled')
        parent.sidebar_frame.rgb_button.configure(state='disabled')
        parent.sidebar_frame.thor_button.configure(state='disabled')
        parent.sidebar_frame.open_thor_button.configure(state='disabled')
        parent.tabview.exposure_entry.configure(state='disabled')
        parent.tabview.sfdi_button.configure(state='disabled')

    else:
        parent.after(100)
        parent.patient_entry.configure(state='normal')
        parent.sidebar_frame.folder_button.configure(state='normal')
        parent.sidebar_frame.white_button.configure(state='normal')
        parent.sidebar_frame.black_button.configure(state='normal')
        parent.sidebar_frame.rgb_button.configure(state='normal')
        parent.sidebar_frame.thor_button.configure(state='normal')
        parent.sidebar_frame.open_thor_button.configure(state='normal')
        parent.tabview.exposure_entry.configure(state='normal')
        parent.tabview.sfdi_button.configure(state='normal')

    parent.after(50, parent.update)
