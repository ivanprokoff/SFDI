from datetime import datetime
import os
#import photo_pipeline_2


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
        for method in ['SFDI', 'infrared', 'photo']:

            folder_name = f'{main_path}/{date}/{patient_id}/{method}'

            if not os.path.exists(folder_name):
                os.mkdir(folder_name)

        for color in ['red', 'green', 'blue']:

            folder_name = f'{main_path}/{date}/{patient_id}/SFDI/{color}'
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)



def return_current_directory(patient_id, main_path='C:/Users/madpl/clinic_data'):
    date = str(datetime.date(datetime.now()))
    folder_id = f'{main_path}/{date}/{patient_id}'
    return f'{main_path}/{date}/{patient_id}'

def predict_hb(parent):
    1
    # parent.renew_current_directory()
    # folder_photo = f'{parent.current_directory}/Photo'
    #
    # pred_dict = photo_pipeline_2.prediction_pipeline.pipeline_for_folder(folder_photo)
    # print(folder_photo)
    # print(pred_dict)
    # args = 'Hb_level='+str(int(pred_dict[-1]['HB_GperL']))+'g/L'
    # parent.insert_log('Predict', args)