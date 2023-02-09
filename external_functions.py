from datetime import datetime
import os


def create_today_directory(main_path='C:/Users/madpl/clinic_data'):

    date = str(datetime.date(datetime.now()))
    date_path = f'{main_path}/{date}'

    if not os.path.exists(date_path):
        os.mkdir(date_path)

def create_patient_directory(patient_id, main_path='C:/Users/madpl/clinic_data'):

    date = str(datetime.date(datetime.now()))
    folder_id = f'{main_path}/{date}/{patient_id}'

    if patient_id and not os.path.exists(folder_id):
        os.mkdir(folder_id)

    if patient_id:
        for measurement in ['SFDI', 'infrared', 'photo']:

            folder_name = f'{main_path}/{date}/{patient_id}/{measurement}'

            if not os.path.exists(folder_name):
                os.mkdir(folder_name)

