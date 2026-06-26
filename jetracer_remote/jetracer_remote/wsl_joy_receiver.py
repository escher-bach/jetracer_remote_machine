#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import socket
import json

class WslJoyReceiver(Node):
    def __init__(self):
        super().__init__('wsl_joy_receiver')
        self.publisher_ = self.create_publisher(Joy, 'joy', 10)
        
        self.declare_parameter('port', 5005)
        port = self.get_parameter('port').value

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        self.sock.setblocking(False)

        # High frequency check for UDP packets
        self.timer = self.create_timer(0.01, self.timer_callback)
        self.get_logger().info(f'UDP Joy receiver listening on port {port}')

    def timer_callback(self):
        try:
            while True:
                data, _ = self.sock.recvfrom(1024)
                joy_data = json.loads(data.decode('utf-8'))
                
                self.get_logger().info(f"Received: axes={[round(a,2) for a in joy_data.get('axes', [])]}, buttons={joy_data.get('buttons', [])}")
                
                msg = Joy()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.axes = [float(a) for a in joy_data.get('axes', [])]
                msg.buttons = [int(b) for b in joy_data.get('buttons', [])]
                
                self.publisher_.publish(msg)
        except BlockingIOError:
            pass
        except Exception as e:
            import traceback
            with open('wsl_crash_log.txt', 'a') as f:
                f.write(traceback.format_exc() + '\n')
            self.get_logger().error(f"Error receiving UDP data: {e} (saved to wsl_crash_log.txt)")

def main(args=None):
    rclpy.init(args=args)
    node = WslJoyReceiver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
