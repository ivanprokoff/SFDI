from datetime import datetime
import os


def create_today_directory(main_path='C:/Users/madpl/clinic_data'):

    date = str(datetime.date(datetime.now()))
    date_path = os.path.join(main_path, date)

    if not os.path.exists(date_path):
        os.mkdir(date_path)


def create_patient_directory(patient_id, main_path='C:/Users/madpl/clinic_data'):

    for measurement in ['SFDI', 'infrared', 'photo']:

        folder_name = f'{main_path}/{patient_id}/{measurement}'

        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

