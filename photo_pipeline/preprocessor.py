from photo_pipeline import loader
import sys
import os
import numpy as np
import pandas as pd

import skimage.color as skcolor

sys.path.append(os.path.join(os.path.dirname(__file__),'nailtracking/'))

import nail_detector

NOT_BRIGHT_IMAGE_ERROR = 'NOT_BRIGHT_IMAGE'
NO_NAILS_FOUND_ERROR = "NO_NAILS_FOUND"
NO_NAILS_IN_GOOD_ROI_ERROR = "NO_NAILS_IN_GOOD_ROI"
NO_GOOD_NAILS_ERROR = "NO_GOOD_NAILS_FOUND_ERROR"
NO_GOOD_SKIN_IMAGES_ERROR = "NO_GOOD_SKIN_IMAGES"


def is_bright_image(img):
    """
    Check whether the image is bright or dark by simple intensity comparison

    :param img:
    :return:
    """
    return np.mean(img) > 130

detector = nail_detector.NailDetector()
good_skin_predictor = loader.load_model('good_skin_predictor.pkl')

def detect_nail_bboxes(image):
    """
    detect bboxes corresponding to nails on the image

    bboxes are returned as (bot,left,top,right)
    :param image: 3d numpy array
    :return: tuple of 2, (bboxes, scores)
    """

    bboxes, scores, labels = detector.predict_bboxes(image)

    #as we dont need labels we return bboxes and scores only
    return bboxes, scores

def cut_image(img,low=0.4,high=0.75):
    """cut image by given low and high borders

    :param img: 3d np.array
    :param low: (float) in the range [0. ... 1.0], should be less than `high`
    :param high:(float) int the range [0. ... 1.0] shoud be greater than `low`
    :return: cutted image
    """
    h,w = img.shape[:2]
    return img[int(low*h):int(high*h),int(low*w):int(high*w),:]

def nail_in_good_ROI(nail_bbox):
    """
    Check whether nail is in good region of interest

    :param nail_bbox:
    :return:
    """
    return nail_bbox[0] < 20 or nail_bbox[0] > 300

def check_img_have_elements(img):
    """check whether image consist of at least one element
    :param img: - image
    :return:
    """
    return np.prod(img.shape) > 0


def get_white_ref_image(image,bot=350, left=400, top=400, right=450):
    """
    Get sub-image of white reference

    :param image: initial input image
    :return:
    """
    return image[bot:top,left:right]

def get_skin_bbox(nail_bbox,shift_x=100,shift_y=0):
    """

    :param nail_bbox:
    :param shift_x:
    :param shift_y:
    :return:
    """
    return [nail_bbox[0] + shift_y, nail_bbox[1] + shift_x,
            nail_bbox[2] + shift_y, nail_bbox[3] + shift_x]


def cut_image_for_bbox(image,bbox):
    """
    Cut subimage using given bbox

    :param image:
    :param bbox:
    :return:
    """
    bot,left,top,right = bbox
    return image[bot:top,left:right]

def get_intensity_percentile(img,q=50):
    """
    Calculate gray-scale intensity percentile of an image

    :param img: input bgr image
    :param q: quantile (from 0 to 100)
    :return: np.float -- percentile
    """
    return np.percentile(skcolor.rgb2gray(img[:,:,::-1]).ravel(),q=q)

def predict_good_skin(skin_cut_image):
    """
    predict whether skin image is homogeneous or not
    using GaussianMixture

    :param skin_cut_image:
    :return:
    """
    features = np.array([get_intensity_percentile(skin_cut_image,q=q) for q in [1,95]])
    features = pd.DataFrame(features.reshape(1,2),columns=['I_perc=1','I_perc=95'])

    labels = good_skin_predictor.predict(features).ravel()

    return labels[0] == 0



def preprocess(image):
    """

    :param image:
    :return:
    """

    result = { "STATUS": "ERROR",
                "ERROR":  "None",
                "NAIL_IMAGES": [],
                "SKIN_IMAGES": [],
                "WHITE_REF_IMAGE":None}

    if not is_bright_image(image):
        result['ERROR'] = NOT_BRIGHT_IMAGE_ERROR
        return result

    nail_bboxes, scores = detect_nail_bboxes(image)

    if nail_bboxes is None or len(nail_bboxes) == 0:
        result['ERROR'] = NO_NAILS_FOUND_ERROR
        return result

    good_nail_bboxes = [bbox for bbox in nail_bboxes if not nail_in_good_ROI(bbox)]

    if good_nail_bboxes is None or len(good_nail_bboxes) == 0:
        result['ERROR'] = NO_NAILS_IN_GOOD_ROI_ERROR
        return result

    nails_images = [cut_image_for_bbox(image,bbox) for bbox in good_nail_bboxes]
    nails_cutted_images = [cut_image(img) for img in nails_images]

    nails_final_images =  [img for img in nails_cutted_images
                               if check_img_have_elements(img)]

    if nails_final_images is None or len(nails_final_images) == 0:
        result['ERROR'] = NO_GOOD_NAILS_ERROR
        return result


    white_ref_image = get_white_ref_image(image)
    skin_bboxes = [get_skin_bbox(nail_bbox) for nail_bbox in good_nail_bboxes]

    skin_images = [cut_image_for_bbox(image,skin_bbox)
                   for skin_bbox in skin_bboxes]

    good_skin_images = [cut_image(skin_img,0.25,0.75) for skin_img in skin_images
                        if check_img_have_elements(cut_image(skin_img,0.25,0.75))]

    skin_final_images = [skin_img for skin_img in good_skin_images
                        if predict_good_skin(skin_img)]

    if good_skin_images is None or len(good_skin_images) == 0:
        result['ERROR'] = NO_GOOD_SKIN_IMAGES_ERROR
        return result

    result['STATUS'] = "OK"
    result['ERROR'] = 'NONE'
    result['NAIL_IMAGES'] = nails_final_images
    result['SKIN_IMAGES'] = skin_final_images
    result['WHITE_REF_IMAGE'] = white_ref_image

    return result