import cv2
import os
import glob


def read_image(img_path):
    """
    read image in BGR channel

    :param img_path:
    :return:
    """
    return cv2.imread(img_path)


def get_images_paths(folder_path):
    """get list of images paths for given folder
    images extension should be .png

    :param folder_path: (str) - path fo folder in string format
    :return: list of str - paths to images
    """
    return glob.glob(os.path.join(folder_path, '*.png'))

def read_folder(folder_path):
    """
    read images with *.png extension given `folder_path`

    :param folder_path:
    :return: list of images (3d np.array) in BGR format
    """

    filepaths = get_images_paths(folder_path)

    if not filepaths:
        return []

    return [read_image(img_path) for img_path in filepaths]


import pickle as pkl
import os


def load_model(model_name):
    """
    load model stored in .pkl format
    :param model_name: (str) for format '<name>.pkl'
    :return: sklearn.model
    """

    model_path = os.path.join(os.path.dirname(__file__),'models', model_name)
    with open(model_path, 'rb') as f:
        model = pkl.load(f)

    return model