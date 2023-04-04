# -*- coding: utf-8 -*-

# import the necessary packages
# from object_detection.utils import label_map_util
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import numpy as np
import cv2
import find_finger as ff


import os
dirname = os.path.dirname(__file__)

_args = {
    "model": os.path.join(dirname,"model/export_model_008/frozen_inference_graph.pb"),
    "labels": os.path.join(dirname,"record/classes.pbtxt"),
    "num_classes": 1,
    "min_confidence": 0.6,
    "class_model": os.path.join(dirname,"model/class_model/p_class_model_1552620432_.h5")}


class NailDetector:

    def __init__(self):

        self.model = tf.Graph()
        self._initialize_model()


    def _initialize_model(self):
        with self.model.as_default():
            print("> ====== loading NAIL frozen graph into memory")
            graphDef = tf.GraphDef()

            with tf.gfile.GFile(_args["model"], "rb") as f:
                serializedGraph = f.read()
                graphDef.ParseFromString(serializedGraph)
                tf.import_graph_def(graphDef, name="")
            # sess = tf.Session(graph=graphDef)
            print(">  ====== NAIL Inference graph loaded.")
            # return graphDef, sess

    def predict_bboxes(self,image):

        with self.model.as_default():
            with tf.Session(graph=self.model) as sess:
                imageTensor = self.model.get_tensor_by_name("image_tensor:0")
                boxesTensor = self.model.get_tensor_by_name("detection_boxes:0")

                scoresTensor = self.model.get_tensor_by_name("detection_scores:0")
                classesTensor = self.model.get_tensor_by_name("detection_classes:0")
                numDetections = self.model.get_tensor_by_name("num_detections:0")


                (H, W) = image.shape[:2]
                output = image.copy()
                img_ff, bin_mask, res = ff.find_hand_old(image.copy())
                image = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
                image = np.expand_dims(image, axis=0)

                (boxes, scores, labels, N) = sess.run(
                        [boxesTensor, scoresTensor, classesTensor, numDetections],
                        feed_dict={imageTensor: image})
                boxes = np.squeeze(boxes)
                scores = np.squeeze(scores)
                labels = np.squeeze(labels)
                confidence_mask = scores>_args['min_confidence']
                
                return self._convert_bboxes(boxes[confidence_mask],H,W),scores[confidence_mask],labels[confidence_mask]

    def _convert_bboxes(self,boxes,H,W):
        """
        convert bboxes from [0,1]x[0,1] to [0,H]x[0,W] range
        """
        bboxes = []
        for box in boxes:
            (startY, startX, endY, endX) = box
            x = int(startX * W)
            y = int(startY * H)
            xe = int(endX * W)
            ye = int(endY * H)

            bboxes.append([y,x,ye,xe])
        return np.array(bboxes)

if __name__ == "__main__":
    image = cv2.imread('test.jpg')

    nail_detector = NailDetector()

    print(nail_detector.predict_bboxes(image=image))