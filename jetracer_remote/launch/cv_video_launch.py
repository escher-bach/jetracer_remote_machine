from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Define Launch Arguments
    cam_name_arg = DeclareLaunchArgument(
        'cam_name',
        default_value='csi_cam_0',
        description='Name of the camera namespace'
    )
    
    topic_name_arg = DeclareLaunchArgument(
        'topic_name',
        default_value='cv_video',
        description='Name of the output topic namespace'
    )
    
    # 2. Define the Node execution block
    cv_video_node = Node(
        package='jetracer_remote',
        executable='cv_video', 
        name='cv_video',
        output='screen',
        parameters=[{
            'camera_name': LaunchConfiguration('cam_name'),
            'topic_name': LaunchConfiguration('topic_name')
        }]
    )

    # 3. Build and return the configuration tree
    return LaunchDescription([
        cam_name_arg,
        topic_name_arg,
        cv_video_node
    ])
