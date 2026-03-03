#!/usr/bin/env python3
import numpy as np
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped
from visualization_msgs.msg import Marker
from rcl_interfaces.msg import SetParametersResult

from wall_follower_rover.visualization_tools import VisualizationTools


class WallFollower(Node):

    def __init__(self):
        super().__init__("wall_follower")
        # Declare parameters to make them available for use
        # DO NOT MODIFY THIS!
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("drive_topic", "/drive")
        self.declare_parameter("side", 1)
        self.declare_parameter("velocity", 1.0)
        self.declare_parameter("desired_distance", 1.0)

        # Fetch constants from the ROS parameter server
        # DO NOT MODIFY THIS! This is necessary for the tests to be able to test varying parameters!
        self.SCAN_TOPIC = self.get_parameter('scan_topic').get_parameter_value().string_value
        self.DRIVE_TOPIC = self.get_parameter('drive_topic').get_parameter_value().string_value
        self.SIDE = self.get_parameter('side').get_parameter_value().integer_value
        self.VELOCITY = self.get_parameter('velocity').get_parameter_value().double_value
        self.DESIRED_DISTANCE = self.get_parameter('desired_distance').get_parameter_value().double_value

        # for PID
        self.PREV_ERROR = 0
        self.TICK_TIME = 0.02
        # This activates the parameters_callback function so that the tests are able
        # to change the parameters during testing.
        # DO NOT MODIFY THIS!
        self.add_on_set_parameters_callback(self.parameters_callback)

        # TODO: Initialize your publishers and subscribers here
        self.drive_commands = self.create_publisher(
            AckermannDriveStamped,
            self.DRIVE_TOPIC,
            10)
        self.lidar_data = self.create_subscription(
            LaserScan,
            self.SCAN_TOPIC,
            self.listener_callback,
            10)
        self.lidar_data

        # TODO: Write your callback functions here
    def listener_callback(self, lidar_msg):
        """
        Filters out ranges to points relevant to the side and position
        of the car. Uses a PID controller to calculate the necessary steering angle.

        :param lidar_msg: A point cloud in LaserScan form.
        """

        a_min, a_max, a_incr = lidar_msg.angle_min, lidar_msg.angle_max, lidar_msg.angle_increment
        A = np.array(lidar_msg.ranges) # ranges array
        a = a_min + np.arange(len(A), dtype=np.float32) * a_incr # angles array

        if self.SIDE == 1:
            a_min, a_max = -math.pi/12, math.pi/2
        else:
            a_min, a_max = -math.pi/2, math.pi/12

        valid_r = (0.2 <= A) & (A <= 5)
        valid_a = (a_min <= a) & (a <= a_max)
        mask = valid_r & valid_a

        if not np.any(mask):
            self.publish_msg(0.0)
            return

        A = A[mask]
        a = a[mask]

        x = A * np.cos(a) # convert from polar to cartesian
        y = A * np.sin(a)

        m, b = np.polyfit(x,y,1)
        line_angle = math.atan(m)
        distance = -b / math.sqrt(m**2 + 1) # fit OLS

        e = (-self.SIDE * self.DESIRED_DISTANCE) - distance
        de = e - self.PREV_ERROR
        prop = 2 * e
        deriv = 0.2 * de/self.TICK_TIME

        self.PREV_ERROR = e
        steering_angle = prop + deriv + 2 * line_angle

        self.publish_msg(steering_angle)

    def publish_msg(self, steering_angle):
        """
        Publishes a AckerMannDrive message.

        :param steering_angle: the steering angle for the drive message.
        """
        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.drive.steering_angle = steering_angle
        msg.drive.speed = self.VELOCITY

        self.drive_commands.publish(msg)

    def parameters_callback(self, params):
        """
        DO NOT MODIFY THIS CALLBACK FUNCTION!

        This is used by the test cases to modify the parameters during testing.
        It's called whenever a parameter is set via 'ros2 param set'.
        """
        for param in params:
            if param.name == 'side':
                self.SIDE = param.value
                self.get_logger().info(f"Updated side to {self.SIDE}")
            elif param.name == 'velocity':
                self.VELOCITY = param.value
                self.get_logger().info(f"Updated velocity to {self.VELOCITY}")
            elif param.name == 'desired_distance':
                self.DESIRED_DISTANCE = param.value
                self.get_logger().info(f"Updated desired_distance to {self.DESIRED_DISTANCE}")
        return SetParametersResult(successful=True)


def main():
    rclpy.init()
    wall_follower = WallFollower()
    rclpy.spin(wall_follower)
    wall_follower.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
