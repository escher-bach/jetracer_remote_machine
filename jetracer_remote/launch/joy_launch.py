from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen'
    )

    teleop_joy_node = Node(
        package='jetracer_remote',
        executable='teleop_joy',
        name='teleop_joy_node',
        output='screen',
        parameters=[
            {'x_speed': 0.3},
            {'y_speed': 0.0},
            {'w_speed': 1.0},
            {'hz': 20.0}
        ]
    )

    return LaunchDescription([
        joy_node,
        teleop_joy_node
    ])
