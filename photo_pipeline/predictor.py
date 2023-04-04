import numpy as np
from photo_pipeline import loader


def get_channel_percentile_for_img(img,chan_num,p):
    return np.percentile(img[:,:,chan_num].ravel(),q=p)

def get_channel_percentile_for_imgs(imgs,chan_num,p):
    """
    calculate median percentile `p` of intensity in color channel `chan_num`
    of images of nails or skin given in `imgs` list of images

    :param imgs: (list of 3d np.array) list of BGR images of nails or skin
    :param chan_num: (int) color channel num from which the data has to be extracted
    :param p: (int or float) percentile in [0, 100] range
    :return: (np.float) - median value of percentile of images
    """
    return np.median([get_channel_percentile_for_img(img,chan_num,p)
                      for img in imgs])

def feature_extractor(preprocessor_result):
    """

    :param preprocessor_result: (dict)
    :return: feature_values, feature_names
    """
    features = []
    feature_names = []

    white_ref_img = preprocessor_result['WHITE_REF_IMAGE']

    for site in ['nail', 'skin']:

        imgs = preprocessor_result['NAIL_IMAGES'] if site =='nail' \
               else preprocessor_result['SKIN_IMAGES']

        for perc in [15, 25, 50, 65, 75]:
            for chan_num, chan in enumerate("BGR"):
                ref = get_channel_percentile_for_img(white_ref_img,chan_num,p=50)
                feature_value = get_channel_percentile_for_imgs(imgs,chan_num,perc)/ref
                features.append(feature_value)
                feature_names.append(f'{site}_{chan}_perc={perc}_norm')

    return np.array(features).reshape(1,-1),np.array(feature_names)


regressor = loader.load_model('hemoglobin_regressor_v2.pkl')

def predict_hemoglobin(features):
    """

    :param features: features
    :return:
    """

    try:
        return regressor.predict(features).ravel()[0]
    except ValueError as e:
        return -1

