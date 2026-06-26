#!/usr/bin/env python3
import sys
import os
import urllib.request
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError
from ament_index_python.packages import get_package_share_directory

class DeepFaceTracking(Node):
    def __init__(self):
        super().__init__('deep_face_tracking')
        
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'deep_face_tracking')
        self.declare_parameter('confidence_threshold', 0.5)
        
        camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        self.conf_threshold = self.get_parameter('confidence_threshold').get_parameter_value().double_value
        
        self.bridge = CvBridge()
        
        # Define model paths
        try:
            pkg_share = get_package_share_directory('jetracer_remote')
            model_dir = os.path.join(pkg_share, 'data')
        except Exception:
            model_dir = '/tmp'
            
        os.makedirs(model_dir, exist_ok=True)
        self.prototxt_path = os.path.join(model_dir, 'deploy.prototxt')
        self.caffemodel_path = os.path.join(model_dir, 'res10_300x300_ssd_iter_140000.caffemodel')

        self.download_models()

        try:
            self.net = cv2.dnn.readNetFromCaffe(self.prototxt_path, self.caffemodel_path)
            self.get_logger().info("Successfully loaded OpenCV DNN Face Detector.")
        except Exception as e:
            self.get_logger().error(f"Failed to load DNN model: {e}")
            self.net = None
        
        self.image_sub = self.create_subscription(
            CompressedImage,
            f"{camera_name}/image_raw/compressed",
            self.callback,
            qos_profile_sensor_data
        )
        self.image_pub = self.create_publisher(
            CompressedImage,
            f"{topic_name}/compressed",
            qos_profile_sensor_data
        )

    def download_models(self):
        prototxt_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
        caffemodel_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        
        if not os.path.exists(self.prototxt_path):
            self.get_logger().info(f"Downloading architecture to {self.prototxt_path}...")
            urllib.request.urlretrieve(prototxt_url, self.prototxt_path)
            
        if not os.path.exists(self.caffemodel_path):
            self.get_logger().info(f"Downloading weights to {self.caffemodel_path} (this may take a moment)...")
            urllib.request.urlretrieve(caffemodel_url, self.caffemodel_path)

    def callback(self, data):
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        if self.net is not None:
            (h, w) = cv_image.shape[:2]
            # Construct a blob from the image
            blob = cv2.dnn.blobFromImage(cv_image, 1.0, (300, 300), (104.0, 177.0, 123.0))
            
            # Pass the blob through the network
            self.net.setInput(blob)
            detections = self.net.forward()
            
            # Loop over the detections
            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                # Filter out weak detections
                if confidence > self.conf_threshold:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    
                    # Draw bounding box and probability
                    text = f"{confidence * 100:.2f}%"
                    y = startY - 10 if startY - 10 > 10 else startY + 10
                    cv2.rectangle(cv_image, (startX, startY), (endX, endY), (0, 255, 0), 2)
                    cv2.putText(cv_image, text, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

        cv2.imshow("Deep Face Tracking (OpenCV DNN)", cv_image)
        cv2.waitKey(1)

        try:
            compressed_msg = self.bridge.cv2_to_compressed_imgmsg(cv_image, dst_format='jpg')
            compressed_msg.header = data.header
            self.image_pub.publish(compressed_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge compression error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = DeepFaceTracking()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down deep_face_tracking node.")
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
