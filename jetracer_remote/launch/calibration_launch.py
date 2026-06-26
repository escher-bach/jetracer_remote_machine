from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    cam_name_arg = DeclareLaunchArgument(
        'cam_name',
        default_value='csi_cam_0',
        description='Name of the camera namespace'
    )
    
    topic_name_arg = DeclareLaunchArgument(
        'topic_name',
        default_value='calibration_image',
        description='Name of the output topic namespace'
    )
    
    calibration_node = Node(
        package='jetracer_remote',
        executable='calibration', 
        name='calibration',
        output='screen',
        parameters=[{
            'camera_name': LaunchConfiguration('cam_name'),
            'topic_name': LaunchConfiguration('topic_name')
        }]
    )

    return LaunchDescription([
        cam_name_arg,
        topic_name_arg,
        calibration_node
    ])
