#!/usr/bin/env python3
import sys
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError
from rcl_interfaces.msg import SetParametersResult

class ColorTracking(Node):
    def __init__(self):
        super().__init__('color_tracking')
        
        self.declare_parameter('camera_name', 'csi_cam_0')
        self.declare_parameter('topic_name', 'color_tracking')
        
        # Color parameters
        self.declare_parameter('Hmin', 110)
        self.declare_parameter('Hmax', 130)
        self.declare_parameter('Smin', 100)
        self.declare_parameter('Smax', 255)
        self.declare_parameter('Vmin', 100)
        self.declare_parameter('Vmax', 255)

        self.add_on_set_parameters_callback(self.parameter_callback)
        
        camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        
        # Local boundaries
        self.lower = np.array([
            self.get_parameter('Hmin').value,
            self.get_parameter('Smin').value,
            self.get_parameter('Vmin').value
        ])
        self.upper = np.array([
            self.get_parameter('Hmax').value,
            self.get_parameter('Smax').value,
            self.get_parameter('Vmax').value
        ])

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
        self.setcolor = False

    def parameter_callback(self, params):
        for param in params:
            if param.name == 'Hmin': self.lower[0] = param.value
            elif param.name == 'Smin': self.lower[1] = param.value
            elif param.name == 'Vmin': self.lower[2] = param.value
            elif param.name == 'Hmax': self.upper[0] = param.value
            elif param.name == 'Smax': self.upper[1] = param.value
            elif param.name == 'Vmax': self.upper[2] = param.value
        return SetParametersResult(successful=True)

    def onMouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.xy[0] = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.xy[1] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.setcolor = True

    def callback(self, data):
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge conversion error: {e}")
            return

        if self.setcolor:
            try:
                x_min = min(self.xy[:,0])
                y_min = min(self.xy[:,1])
                x_max = max(self.xy[:,0])
                y_max = max(self.xy[:,1])
                
                # Check bounds to avoid empty ROI
                if x_max > x_min and y_max > y_min:
                    Roi = cv_image[y_min:y_max, x_min:x_max]
                    hsv_roi = cv2.cvtColor(Roi, cv2.COLOR_BGR2HSV)

                    # Get true min/max over the entire ROI
                    H_min = int(np.min(hsv_roi[:, :, 0]))
                    S_min = int(np.min(hsv_roi[:, :, 1]))
                    V_min = int(np.min(hsv_roi[:, :, 2]))
                    
                    H_max = int(np.max(hsv_roi[:, :, 0]))
                    S_max = int(np.max(hsv_roi[:, :, 1]))
                    V_max = int(np.max(hsv_roi[:, :, 2]))

                    # HSV range adjustment with proper OpenCV bounds
                    H_max = min(H_max + 5, 179)
                    H_min = max(H_min - 5, 0)
                    S_min = max(S_min - 20, 0)
                    V_min = max(V_min - 20, 0)
                    S_max = 255
                    V_max = 255

                    # Self-update parameters (acts as Client)
                    new_params = [
                        rclpy.Parameter('Hmin', rclpy.Parameter.Type.INTEGER, H_min),
                        rclpy.Parameter('Hmax', rclpy.Parameter.Type.INTEGER, H_max),
                        rclpy.Parameter('Smin', rclpy.Parameter.Type.INTEGER, S_min),
                        rclpy.Parameter('Smax', rclpy.Parameter.Type.INTEGER, S_max),
                        rclpy.Parameter('Vmin', rclpy.Parameter.Type.INTEGER, V_min),
                        rclpy.Parameter('Vmax', rclpy.Parameter.Type.INTEGER, V_max),
                    ]
                    self.set_parameters(new_params)
            except Exception as e:
                self.get_logger().error(f"Color selection failed: {e}")
            
            self.setcolor = False
        else:
            hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.lower, self.upper)

            # Noise Reduction: Morphological operations
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.dilate(mask, kernel, iterations=2)

            res = cv2.bitwise_and(cv_image, cv_image, mask=mask)
            cv2.imshow("Color Tracking", res)

        cv2.putText(cv_image, f"Upper : {self.upper}", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        cv2.putText(cv_image, f"Lower : {self.lower}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

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
    node = ColorTracking()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down color_tracking node.")
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
