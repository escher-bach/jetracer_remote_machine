#!/usr/bin/env python3

import sys
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

msg = """
Reading from the keyboard  and Publishing to Twist!
---------------------------
Moving around:
   u    i    o         ^
   j    k    l       < v >
   m    ,    .

For Holonomic mode (strafing), hold down the shift key:
---------------------------
   U    I    O
   J    K    L
   M    <    >

t : up (+z)
b : down (-z)

anything else : stop

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%

CTRL-C to quit
"""

moveBindings = {
    'i': (1, 0, 0, 0),
    'o': (1, 0, 0, -1),
    'j': (0, 0, 0, 1),
    'l': (0, 0, 0, -1),
    'u': (1, 0, 0, 1),
    ',': (-1, 0, 0, 0),
    '.': (-1, 0, 0, 1),
    'm': (-1, 0, 0, -1),
    'O': (1, -1, 0, 0),
    'I': (1, 0, 0, 0),
    'J': (0, 1, 0, 0),
    'L': (0, -1, 0, 0),
    'U': (1, 1, 0, 0),
    '<': (-1, 0, 0, 0),
    '>': (-1, -1, 0, 0),
    'M': (-1, 1, 0, 0),
    't': (0, 0, 1, 0),
    'k': (0, 0, 0, 0),
    ' ': (0, 0, 0, 0),
    'b': (0, 0, -1, 0),
    'A': (1, 0, 0, 0),
    'B': (-1, 0, 0, 0),
    'C': (0, 0, 0, -1),
    'D': (0, 0, 0, 1),
}

speedBindings = {
    'q': (1.1, 1.1),
    'z': (.9, .9),
    'w': (1.1, 1),
    'x': (.9, 1),
    'e': (1, 1.1),
    'c': (1, .9),
}

def getKey(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def vels(speed, turn):
    return "currently:\tspeed %s\tturn %s " % (speed, turn)

def main(args=None):
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init(args=args)
    node = rclpy.create_node('teleop_twist_keyboard')

    node.declare_parameter('speed', 0.5)
    node.declare_parameter('turn', 1.0)

    speed = node.get_parameter('speed').value
    turn = node.get_parameter('turn').value

    pub = node.create_publisher(Twist, 'cmd_vel', 10)

    x = 0.0
    y = 0.0
    z = 0.0
    th = 0.0
    status = 0

    try:
        print(msg)
        print(vels(speed, turn))
        while rclpy.ok():
            key = getKey(settings)
            
            if key != '':
                if key in moveBindings.keys():
                    x = moveBindings[key][0]
                    y = moveBindings[key][1]
                    z = moveBindings[key][2]
                    th = moveBindings[key][3]
                    
                    twist = Twist()
                    twist.linear.x = float(x * speed)
                    twist.linear.y = float(y * speed)
                    twist.linear.z = float(z * speed)
                    twist.angular.x = 0.0
                    twist.angular.y = 0.0
                    twist.angular.z = float(th * turn)
                    pub.publish(twist)

                elif key in speedBindings.keys():
                    speed = speed * speedBindings[key][0]
                    turn = turn * speedBindings[key][1]

                    print(vels(speed, turn))
                    if (status == 14):
                        print(msg)
                    status = (status + 1) % 15
                    
                else:
                    x = 0.0
                    y = 0.0
                    z = 0.0
                    th = 0.0
                    if (key == '\x03'):
                        break

    except Exception as e:
        print(e)

    finally:
        twist = Twist()
        twist.linear.x = 0.0
        twist.linear.y = 0.0
        twist.linear.z = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = 0.0
        pub.publish(twist)

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
