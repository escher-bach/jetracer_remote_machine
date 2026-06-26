#!/usr/bin/env python3
import sys
import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError

class ImageConverter(Node):
    def __init__(self):
        # Initialize the Node with the executable name
        super().__init__('image_converter')
        
        # 1. Parameter Declaration and Retrieval
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'cv_video')
        
        camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        
        self.bridge = CvBridge()
        
        # 2. Subscription and Publisher Initialization utilizing Sensor Data QoS
        # This profile enforces BEST_EFFORT reliability and a KEEP_LAST history depth of 5.
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
            # Convert ROS 2 CompressedImage to OpenCV BGR8 Mat
            img = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        # Core operations on the frame
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        cv2.imshow("OpenCV Video window", gray)
        # 1ms delay allows OpenCV's highgui thread to process window events
        cv2.waitKey(1)

        try:
            # Convert OpenCV Gray Mat back to ROS 2 CompressedImage
            compressed_msg = self.bridge.cv2_to_compressed_imgmsg(gray, dst_format='jpg')
            
            # Reattach the original header to maintain temporal and spatial (TF) frame continuity
            compressed_msg.header = data.header
            
            self.image_pub.publish(compressed_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge compression error: {e}")

def main(args=None):
    rclpy.init(args=args)
    ic = ImageConverter()
    
    try:
        rclpy.spin(ic)
    except KeyboardInterrupt:
        ic.get_logger().info("Shutting down image_converter node.")
    finally:
        # Explicit cleanup of system resources
        cv2.destroyAllWindows()
        ic.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
