from datetime import datetime
import os
#import photo_pipeline_2


def create_today_directory(main_path='C:/Users/madpl/clinic_data'):
    date = str(datetime.date(datetime.now()))
    date_path = f'{main_path}/{date}'
    for mode in ['SFDI', 'Photo', 'Infrared']:
        date_path = f'{main_path}/{mode}/{date}'
        if not os.path.exists(date_path):
            os.mkdir(date_path)


def create_patient_directory(patient_id, modes=['SFDI', 'Infrared', 'photo'], main_path='C:/Users/madpl/clinic_data'):
    date = str(datetime.date(datetime.now()))

    for method in modes:
        folder_id = f'{main_path}/{method}/{date}/{patient_id}'

        if patient_id and not os.path.exists(folder_id):
            os.mkdir(folder_id)


            for color in ['red', 'green', 'blue']:

                folder_name = f'{main_path}/SFDI/{date}/{patient_id}/{color}'
                if not os.path.exists(folder_name):
                    os.mkdir(folder_name)



def return_current_directory(patient_id, mode='SFDI', main_path='C:/Users/madpl/clinic_data'):
    date = str(datetime.date(datetime.now()))
    return f'{main_path}/{mode}/{date}/{patient_id}'

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