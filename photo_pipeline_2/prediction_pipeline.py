from photo_pipeline import loader
from photo_pipeline import preprocessor
from photo_pipeline import predictor
import pandas as pd

NO_IMAGES_FOUND_ERROR = "NO_IMAGES_FOUND"
MODEL_ERROR = "MODEL_ERROR_CHECK_INPUTS"

def pipeline_for_image(image):
    """
    get BGR image of hand with nails
    and attempts to predict hemoglobin value
    in case of wrong folder or

    :param image: (3d np.array) - raw image of nails
    :return: result (dict)
    """

    result = {"STATUS"  : "ERROR",
              "ERROR"   : "DEFAULT_ERROR",
              "HB_GperL": "NONE"}

    preprocessing_result = preprocessor.preprocess(image)

    if preprocessing_result['STATUS'] == 'ERROR':
        result['ERROR'] =  preprocessing_result['ERROR']
        return result

    features,feature_names = predictor.feature_extractor(preprocessing_result)
    hb_value = predictor.predict_hemoglobin(pd.DataFrame(features,columns=feature_names))

    if hb_value != -1:
        result["STATUS"] = "OK"
        result['ERROR'] = "NONE"
        result["HB_GperL"] = hb_value
    else:
        result["STATUS"] = "ERROR"
        result["ERROR"] = MODEL_ERROR

    return result

def pipeline_for_folder(img_folder_path):
    """
    get folder
    :param img_folder_path:
    :return: list of results for all images found in folder
    """
    result = {"STATUS": "ERROR",
              "ERROR": "DEFAULT_ERROR",
              "HB_GperL": "NONE"}

    images_paths = loader.get_images_paths(img_folder_path)
    images = loader.read_folder(img_folder_path)

    if not images:
        result['ERROR'] = NO_IMAGES_FOUND_ERROR
        return [result]

    results = []

    for path,image in zip(images_paths,images):
        result = pipeline_for_image(image)
        result['IMG_PATH'] = path
        results.append(result)

    return results
