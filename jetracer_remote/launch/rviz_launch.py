import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def _launch_rviz(context):
    ns = LaunchConfiguration('namespace').perform(context)
    pkg_dir = get_package_share_directory('jetracer_remote')
    rviz_config_path = os.path.join(pkg_dir, 'rviz', 'jetracer.rviz')

    # When namespace is set, remap the standard topics rviz2 uses.
    # When empty, no remapping is needed (default single-robot behavior).
    remappings = []
    if ns:
        for topic in ['/tf', '/tf_static', '/initialpose', '/goal_pose']:
            remappings.append((topic, f'/{ns}{topic}'))

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        remappings=remappings,
        output='screen'
    )
    return [rviz_node]

def generate_launch_description():
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace (e.g. bot1)'
    )

    return LaunchDescription([
        namespace_arg,
        OpaqueFunction(function=_launch_rviz)
    ])

