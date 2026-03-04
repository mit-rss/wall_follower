import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped

class SafetyTester(Node):

    def __init__(self):
        super().__init__("safety_tester")
        # Declare parameters to make them available for use
        # DO NOT MODIFY THIS!
        self.declare_parameter("drive_topic", "/vesc/high_level/input/nav_1")
        self.declare_parameter("drive_speed",1)

        # Fetch constants from the ROS parameter server
        # DO NOT MODIFY THIS! This is necessary for the tests to be able to test varying parameters!
        self.DRIVE_TOPIC = self.get_parameter('drive_topic').get_parameter_value().string_value
        self.SPEED = self.get_parameter('drive_speed').get_parameter_value().double_value

        self.timer = self.create_timer(0.05, self.drive_timer_callback)
        ### Publishers ###
        self.drive_test_publisher = self.create_publisher(
            AckermannDriveStamped,
            self.DRIVE_TOPIC,
            10
        )

        # # https://docs.ros.org/en/jade/api/ackermann_msgs/html/msg/AckermannDriveStamped.html
        # new_msg = AckermannDriveStamped()

        # # https://docs.ros.org/en/jade/api/ackermann_msgs/html/msg/AckermannDrive.html
        # drive_command = new_msg.drive
        # drive_command.speed = 1.0
        # drive_command.acceleration = 0.0
        # # jerk indicates a desired absolute rate of acceleration change in either direction (increasing or decreasing).
        # drive_command.jerk = 0.0

        # self.drive_test_publisher.publish(new_msg)

    def drive_timer_callback(self):
        """ Basic Drive Command """
        new_msg = AckermannDriveStamped()
        drive_command = new_msg.drive
        drive_command.speed = self.SPEED
        drive_command.acceleration = 0.0
        drive_command.jerk = 0.0
        self.drive_test_publisher.publish(new_msg)


def main():
    rclpy.init()
    safety_tester = SafetyTester()
    rclpy.spin(safety_tester)
    safety_tester.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
