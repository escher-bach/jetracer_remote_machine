#!/usr/bin/env python3
import sys
import cv2
import rclpy
import numpy as np
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage, CameraInfo
from cv_bridge import CvBridge, CvBridgeError

class Calibration(Node):
    def __init__(self):
        super().__init__('calibration')
        
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'calibration_image')
        
        camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        
        self.bridge = CvBridge()
        
        self.image_sub = self.create_subscription(
            CompressedImage,
            f"{camera_name}/image_raw/compressed",
            self.callback,
            qos_profile_sensor_data
        )
        self.image_info_sub = self.create_subscription(
            CameraInfo,
            f"{camera_name}/camera_info",
            self.info_callback,
            qos_profile_sensor_data
        )
        self.image_pub = self.create_publisher(
            CompressedImage,
            f"{topic_name}/compressed",
            qos_profile_sensor_data
        )
        
        self.mtx = None
        self.dist = None

    def info_callback(self, data):
        self.dist = np.array(data.d).reshape(1, 5)
        self.mtx = np.array(data.k).reshape(3, 3)

    def callback(self, data):
        try:
            img = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        if self.mtx is None or self.dist is None:
            self.get_logger().warn("Camera info not received yet, skipping frame.", throttle_duration_sec=1.0)
            return

        h, w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))

        # undistort
        dst = cv2.undistort(img, self.mtx, self.dist, None, newcameramtx)
        
        # crop the image
        x, y, w_roi, h_roi = roi
        dst = dst[y:y+h_roi, x:x+w_roi]

        cv2.imshow("Image window", img)
        cv2.imshow("Calibration Image window", dst)
        cv2.waitKey(3)

        try:
            compressed_msg = self.bridge.cv2_to_compressed_imgmsg(dst, dst_format='jpg')
            compressed_msg.header = data.header
            self.image_pub.publish(compressed_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge compression error: {e}")

def main(args=None):
    rclpy.init(args=args)
    calib_node = Calibration()
    
    try:
        rclpy.spin(calib_node)
    except KeyboardInterrupt:
        calib_node.get_logger().info("Shutting down calibration node.")
    finally:
        cv2.destroyAllWindows()
        calib_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
