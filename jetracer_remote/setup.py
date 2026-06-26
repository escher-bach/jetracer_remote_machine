from setuptools import setup
import os
from glob import glob

package_name = 'jetracer_remote'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'data'), glob('data/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='User',
    maintainer_email='user@todo.todo',
    description='Jetracer remote operator station (teleop, vision, RViz)',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'teleop_key = jetracer_remote.teleop_key:main',
            'teleop_joy = jetracer_remote.teleop_joy:main',
            'wsl_joy_receiver = jetracer_remote.wsl_joy_receiver:main',
            'cv_video = jetracer_remote.cv_video:main',
            'calibration = jetracer_remote.calibration:main',
            'contours = jetracer_remote.contours:main',
            'motion_detect = jetracer_remote.motion_detect:main',
            'object_tracking = jetracer_remote.object_tracking:main',
            'pose = jetracer_remote.pose:main',
            'face_detect = jetracer_remote.face_detect:main',
            'color_tracking = jetracer_remote.color_tracking:main',
            'deep_face_tracking = jetracer_remote.deep_face_tracking:main'
        ],
    },
)
