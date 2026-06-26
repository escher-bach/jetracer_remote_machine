#!/usr/bin/env python3
import sys
import cv2
import random
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError

class Contours(Node):
    def __init__(self):
        super().__init__('contours')
        
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'contours_image')
        
        camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        
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

    def callback(self, data):
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        edges_img = cv2.Canny(cv_image, 50, 200)
        contours_img = cv2.cvtColor(edges_img, cv2.COLOR_GRAY2BGR)
        
        contours, hierarchy = cv2.findContours(edges_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        for i in range(len(contours)):
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            cv2.drawContours(contours_img, contours, i, color, 1)

        cv2.imshow("Image window", cv_image)
        cv2.imshow("Edges window", edges_img)
        cv2.imshow("Contours window", contours_img)
        cv2.waitKey(1)

        try:
            compressed_msg = self.bridge.cv2_to_compressed_imgmsg(contours_img, dst_format='jpg')
            compressed_msg.header = data.header
            self.image_pub.publish(compressed_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge compression error: {e}")

def main(args=None):
    rclpy.init(args=args)
    contours_node = Contours()
    
    try:
        rclpy.spin(contours_node)
    except KeyboardInterrupt:
        contours_node.get_logger().info("Shutting down contours node.")
    finally:
        cv2.destroyAllWindows()
        contours_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
