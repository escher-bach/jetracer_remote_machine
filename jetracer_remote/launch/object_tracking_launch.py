from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    namespace_arg = DeclareLaunchArgument('namespace', default_value='', description='Robot namespace (e.g. bot1)')
    cam_name_arg = DeclareLaunchArgument('cam_name', default_value='csi_cam_0', description='Camera namespace')
    topic_name_arg = DeclareLaunchArgument('topic_name', default_value='object_tracking', description='Topic namespace')
    
    node = Node(
        package='jetracer_remote',
        executable='object_tracking', 
        name='object_tracking',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[{
            'camera_name': LaunchConfiguration('cam_name'),
            'topic_name': LaunchConfiguration('topic_name')
        }]
    )

    return LaunchDescription([namespace_arg, cam_name_arg, topic_name_arg, node])
