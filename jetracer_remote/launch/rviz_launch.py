import os
import tempfile
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def _launch_rviz(context):
    ns = LaunchConfiguration('namespace').perform(context)
    pkg_dir = get_package_share_directory('jetracer_remote')
    rviz_template_path = os.path.join(pkg_dir, 'rviz', 'jetracer.rviz')

    # Read the template and substitute the namespace placeholder.
    # With a namespace: {namespace}/scan  ->  /bot1/scan
    # Without:          {namespace}/scan  ->  /scan
    with open(rviz_template_path, 'r') as f:
        rviz_content = f.read()

    ns_prefix = f'/{ns}' if ns else ''
    rviz_content = rviz_content.replace('{namespace}', ns_prefix)

    # Write the resolved config to a temp file that persists for the
    # lifetime of the rviz2 process.
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.rviz', prefix='jetracer_', delete=False
    )
    tmp.write(rviz_content)
    tmp.close()

    # When namespace is set, remap /tf and /tf_static so rviz2
    # subscribes to the namespaced transform topics.
    remappings = []
    if ns:
        for topic in ['/tf', '/tf_static']:
            remappings.append((topic, f'/{ns}{topic}'))

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', tmp.name],
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

