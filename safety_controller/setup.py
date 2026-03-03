import glob
import os

from setuptools import find_packages, setup

package_name = 'safety_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            'share/' + package_name,
            ['safety_controller/params.yaml'],
        ),
        (
            'share/' + package_name + '/launch',
            glob.glob(os.path.join('launch', '*.launch.py')),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='racecar',
    maintainer_email='racecar@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'controller = safety_controller.safety_controller:main',
            'tester = safety_controller.safety_tester:main',
            'logger = safety_controller.logger_node:main'
        ],
    },
)
