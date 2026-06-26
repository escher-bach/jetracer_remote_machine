#!/usr/bin/env python3
import sys
import os
import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError
from ament_index_python.packages import get_package_share_directory

class FaceDetect(Node):
    def __init__(self):
        super().__init__('face_detect')
        
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'face_detect')
        
        # Default the XML path to the one installed in the package share directory
        try:
            pkg_share = get_package_share_directory('jetracer_remote')
            default_xml = os.path.join(pkg_share, 'data', 'haarcascade_frontalface_alt2.xml')
        except Exception as e:
            self.get_logger().warn(f"Could not find package share directory: {e}")
            default_xml = "../data/haarcascade_frontalface_alt2.xml"

        self.declare_parameter('file_name', default_xml)
        
        camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        self.file_name = self.get_parameter('file_name').get_parameter_value().string_value
        
        self.bridge = CvBridge()
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
        
        try:
            self.face_cascade = cv2.CascadeClassifier(self.file_name)
            if self.face_cascade.empty():
                self.get_logger().error(f"Failed to load cascade classifier from {self.file_name}")
        except Exception as e:
            self.get_logger().error(f"Exception loading cascade: {e}")

    def callback(self, data):
        try:
            frame = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_gray = cv2.equalizeHist(frame_gray)

        if hasattr(self, 'face_cascade') and not self.face_cascade.empty():
            faces = self.face_cascade.detectMultiScale(frame_gray, 1.2, 5, 0, (50, 50))
            for (x, y, w, h) in faces:
                frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("Face detection", frame)
        cv2.waitKey(1)

        try:
            compressed_msg = self.bridge.cv2_to_compressed_imgmsg(frame, dst_format='jpg')
            compressed_msg.header = data.header
            self.image_pub.publish(compressed_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge compression error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = FaceDetect()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down face_detect node.")
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
