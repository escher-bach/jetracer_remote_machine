#!/usr/bin/env python3
import sys
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError

class ObjectTracking(Node):
    def __init__(self):
        super().__init__('object_tracking')
        
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'object_tracking')
        self.declare_parameter('tracker_type', 'CSRT') # Default updated to CSRT
        
        camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        self.tracker_type = self.get_parameter('tracker_type').get_parameter_value().string_value
        
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

        self.xy = np.array([(0,0), (0,0)])
        self.drawing = False
        self.setObject = False
        self.bbox = (0, 0, 0, 0)
        self.tracker = None

    def onMouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.xy[0] = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.xy[1] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.setObject = True

    def callback(self, data):
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        if self.setObject:
            try:
                x_min = min(self.xy[:,0])
                y_min = min(self.xy[:,1])
                x_max = max(self.xy[:,0])
                y_max = max(self.xy[:,1])
                w = x_max - x_min
                h = y_max - y_min
                self.bbox = (x_min, y_min, w, h)

                # Modern trackers available in standard OpenCV 4.5+
                if self.tracker_type == 'CSRT':
                    self.tracker = cv2.TrackerCSRT_create()
                elif self.tracker_type == 'KCF':
                    self.tracker = cv2.TrackerKCF_create()
                elif self.tracker_type == 'MIL':
                    self.tracker = cv2.TrackerMIL_create()
                else:
                    self.get_logger().warn(f"Tracker {self.tracker_type} not supported, falling back to CSRT.")
                    self.tracker_type = 'CSRT'
                    self.tracker = cv2.TrackerCSRT_create()

                # Initialize tracker with first frame and bounding box
                ok = self.tracker.init(cv_image, self.bbox)
                if not ok:
                    self.tracker = None
            except Exception as e:
                self.get_logger().error(f"Error initializing tracker: {e}")
                self.tracker = None

            self.setObject = False
        else:
            if self.tracker is not None:
                # Update tracker
                ok, bbox = self.tracker.update(cv_image)

                # Draw bounding box
                if ok:
                    # Tracking success
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(cv_image, p1, p2, (255, 0, 0), 2)
                else:
                    # Tracking failure
                    cv2.putText(cv_image, "Tracking failure detected", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

                # Display tracker type on frame
                cv2.putText(cv_image, self.tracker_type + " Tracker", (30, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)

        if self.drawing:
            cv2.rectangle(cv_image, tuple(self.xy[0]), tuple(self.xy[1]), (0, 255, 0), 2)
            cv2.line(cv_image, tuple(self.xy[0]), tuple(self.xy[1]), (255, 0, 0), 2)

        cv2.imshow("Image window", cv_image)
        cv2.setMouseCallback("Image window", self.onMouse)
        cv2.waitKey(1)

        try:
            compressed_msg = self.bridge.cv2_to_compressed_imgmsg(cv_image, dst_format='jpg')
            compressed_msg.header = data.header
            self.image_pub.publish(compressed_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge compression error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ObjectTracking()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down object_tracking node.")
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
