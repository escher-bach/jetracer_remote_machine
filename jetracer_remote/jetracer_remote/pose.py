#!/usr/bin/env python3
import sys
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage, CameraInfo
from cv_bridge import CvBridge, CvBridgeError

class PoseDetection(Node):
    def __init__(self):
        super().__init__('pose_detection')
        
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'AR_image')
        
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

        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.objp = np.zeros((5*7, 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:7, 0:5].T.reshape(-1, 2)
        self.axis = np.float32([[0,0,0], [0,3,0], [3,3,0], [3,0,0],
                                [0,0,-3], [0,3,-3], [3,3,-3], [3,0,-3]])

    def info_callback(self, data):
        self.dist = np.array(data.d).reshape(1, 5)
        self.mtx = np.array(data.k).reshape(3, 3)

    def callback(self, data):
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        if self.mtx is None or self.dist is None:
            self.get_logger().warn("Camera info not received yet, skipping frame.", throttle_duration_sec=1.0)
            return

        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, (7, 5), None, cv2.CALIB_CB_FAST_CHECK)
        
        if ret == True:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
            # Find the rotation and translation vectors
            ret, rvecs, tvecs = cv2.solvePnP(self.objp, corners2, self.mtx, self.dist)
            # Project 3D points to image plane
            imgpts, jac = cv2.projectPoints(self.axis, rvecs, tvecs, self.mtx, self.dist)

            imgpts = np.int32(imgpts).reshape(-1, 2)
            # Draw ground floor in green
            cv_image = cv2.drawContours(cv_image, [imgpts[:4]], -1, (0, 255, 0), -3)
            # Draw pillars in blue color
            for i, j in zip(range(4), range(4, 8)):
                cv_image = cv2.line(cv_image, tuple(imgpts[i]), tuple(imgpts[j]), (255, 0, 0), 3)
            # Draw top layer in red color
            cv_image = cv2.drawContours(cv_image, [imgpts[4:]], -1, (0, 0, 255), 3)

        cv2.imshow('3D Image window', cv_image)
        cv2.waitKey(1)

        try:
            compressed_msg = self.bridge.cv2_to_compressed_imgmsg(cv_image, dst_format='jpg')
            compressed_msg.header = data.header
            self.image_pub.publish(compressed_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge compression error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = PoseDetection()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down pose node.")
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
