#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class TeleopJoy(Node):
    def __init__(self):
        super().__init__('teleop_joy')
        
        self.declare_parameter('x_speed', 0.3)
        self.declare_parameter('y_speed', 0.0)
        self.declare_parameter('w_speed', 1.0)
        self.declare_parameter('hz', 20.0)

        self.x_speed = self.get_parameter('x_speed').value
        self.y_speed = self.get_parameter('y_speed').value
        self.w_speed = self.get_parameter('w_speed').value
        hz = self.get_parameter('hz').value

        self.active = 0
        self.cmd = Twist()
        
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.joy_sub = self.create_subscription(Joy, '/joy', self.joy_callback, 10)
        
        # Timer to continuously publish Twist messages at specified hz
        self.timer = self.create_timer(1.0 / hz, self.timer_callback)
        self.get_logger().info("teleop_joy node started! Waiting for /joy messages with button 6 (Back) pressed...")

    def joy_callback(self, msg):
        # Button 6 is typically LB or Select/Back depending on the controller
        if len(msg.buttons) > 6 and msg.buttons[6] == 1:
            if len(msg.axes) > 3:
                self.cmd.linear.x = float(self.x_speed * msg.axes[3])
            if len(msg.axes) > 0:
                self.cmd.angular.z = float(self.w_speed * msg.axes[0])
            if self.active == 0:
                self.get_logger().info(f"Deadman pressed! Driving: linear={self.cmd.linear.x}, angular={self.cmd.angular.z}")
            self.active = 1
        else:
            self.cmd = Twist()
            self.cmd.linear.x = 0.0
            self.cmd.angular.z = 0.0
            self.active = 0

    def timer_callback(self):
        if self.active == 1:
            self.cmd_pub.publish(self.cmd)
        else:
            self.cmd_pub.publish(self.cmd)

def main(args=None):
    rclpy.init(args=args)
    teleop_joy = TeleopJoy()
    try:
        rclpy.spin(teleop_joy)
    except KeyboardInterrupt:
        pass
    finally:
        twist = Twist()
        teleop_joy.cmd_pub.publish(twist)
        teleop_joy.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
