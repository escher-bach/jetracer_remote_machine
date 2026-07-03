from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    namespace_arg = DeclareLaunchArgument('namespace', default_value='', description='Robot namespace (e.g. bot1)')

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        namespace=LaunchConfiguration('namespace'),
        output='screen'
    )

    teleop_joy_node = Node(
        package='jetracer_remote',
        executable='teleop_joy',
        name='teleop_joy_node',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[
            {'x_speed': 0.3},
            {'y_speed': 0.0},
            {'w_speed': 1.0},
            {'hz': 20.0}
        ]
    )

    return LaunchDescription([
        namespace_arg,
        joy_node,
        teleop_joy_node
    ])
