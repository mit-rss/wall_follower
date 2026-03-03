import glob
import os
from setuptools import find_packages
from setuptools import setup

package_name = 'wall_follower_rover'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/'+package_name, ['package.xml', "wall_follower_rover/params.yaml"]),
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/wall_follower_rover/launch', glob.glob(os.path.join('launch', '*launch.xml'))),
        ('share/wall_follower_rover/launch', glob.glob(os.path.join('launch', '*launch.py')))],

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Sebastian',
    maintainer_email='sebastianag2002@gmail.com',
    description='Wall Follower ROS2 Package',
    license='Apache License, Version 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'wall_follower = wall_follower_rover.wall_follower:main',
            'viz_example = wall_follower_rover.viz_example:main',
            'test_wall_follower = wall_follower_rover.test_wall_follower:main',
        ],
    },
)
