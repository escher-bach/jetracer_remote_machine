#!/usr/bin/env python3
import sys
import cv2
import datetime
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError

class MotionDetect(Node):
    def __init__(self):
        super().__init__('motion_detect')
        
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'motion_detect')
        
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

        self.avg = None

    def callback(self, data):
        try:
            frame = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        # Convert the frame to gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Gaussian blur the frame to avoid misjudgment caused by noise
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.avg is None:
            self.avg = gray.copy().astype("float")

        # Background update
        cv2.accumulateWeighted(gray, self.avg, 0.3)

        # Compare the difference between the new frame and the background
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        text = "Unoccupied"
        for c in contours:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < 1500:
                continue

            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = "Occupied"

        # draw the text and timestamp on the frame
        if text == "Occupied":
            cv2.putText(frame, f"Status: {text}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        cv2.imshow("Frame Image", frame)
        cv2.imshow("Frame Delta", frameDelta)
        cv2.waitKey(1)

        try:
            compressed_msg = self.bridge.cv2_to_compressed_imgmsg(gray, dst_format='jpg')
            compressed_msg.header = data.header
            self.image_pub.publish(compressed_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge compression error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = MotionDetect()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down motion_detect node.")
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
