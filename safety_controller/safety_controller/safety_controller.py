import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped

class SafetyController(Node):

    def __init__(self):
        super().__init__("safety_controller")
        # Declare parameters to make them available for use
        # DO NOT MODIFY THIS!
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("drive_topic_listen", "/vesc/high_level/input/nav_1") # publish to the highest priority to override other drive commands
        self.declare_parameter('drive_topic_publish', "/vesc/high_level/input/nav_0")
        self.declare_parameter("safety_radius", 0.5)
        self.declare_parameter("safety_controller_const", 0.1)
        self.declare_parameter("logger_topic", "/crash_points")

        # Fetch constants from the ROS parameter server
        # DO NOT MODIFY THIS! This is necessary for the tests to be able to test varying parameters!
        self.SCAN_TOPIC = self.get_parameter('scan_topic').get_parameter_value().string_value
        self.DRIVE_TOPIC_LISTEN = self.get_parameter('drive_topic_listen').get_parameter_value().string_value
        self.DRIVE_TOPIC_PUBLISH = self.get_parameter('drive_topic_publish').get_parameter_value().string_value
        self.SAFETY_RADIUS = self.get_parameter('safety_radius').get_parameter_value().value
        self.SAFETY_CONTROLLER_CONST = self.get_parameter('safety_controller_const').get_parameter_value().value
        self.LOGGER_TOPIC = self.get_parameter('logger_topic').get_parameter_value().string_value
        ### Subscribers ###
        self.lidar_subscriber = self.create_subscription(
            LaserScan,
            self.SCAN_TOPIC,
            self.lidar_callback,
            10
        )

        self.drive_subscriber = self.create_subscription(
            AckermannDriveStamped,
            self.DRIVE_TOPIC_LISTEN,
            self.drive_callback,
            10
        )

        ### Publishers ###
        self.stop_publisher = self.create_publisher(
            AckermannDriveStamped,
            self.DRIVE_TOPIC_PUBLISH,
            10
        )

        # the static transform from the base link frame to the lidar frame
        self.base_to_lidar = np.array([
            [1.0, 0.0, 0.0, 0.275],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

        self.lidar_msg = None


    def get_lidar_subset_calculator(self, lidar_angle_min, lidar_angle_max, lidar_angle_increment, lidar_ranges):
        """
        Returns a function tuned to the lidar's base parameters (lidar_angle_min, lidar_angle_max, and lidar_angle_increment)
        that returns points within an angle range.

        Args:
            lidar_angle_min (float): The minimum angle supported by the lidar
            lidar_angle_max (float): The maximum angle supported by the lidar
            lidar_angle_increment (float): The size of the increments in the range [lidar_angle_min, lidar_angle_max]
            lidar_ranges (1D Array): The original lidar data, an indexed by angle with values corresponding to the distance of the point
            from the lidar
        """
        def subset_calculator(angle_range = [lidar_angle_min, lidar_angle_max], distance_range = [0, float("inf")]):
            """
            Returns the cartesian coordinates of the lidar points within a given range of angles
            and a given distance range.

            Args:
                angle_range (1D Array): The given range of angles
                distance_range (1D Array): The given range of distance
            """
            angle_min, angle_max = angle_range
            distance_min, distance_max = distance_range

            # Angle Subset
            if angle_min > angle_max:
                # Swap angles if given in wrong order
                angle_min, angle_max = angle_max, angle_min

            #clip angles to the minimum and maximum angles supported by the lidar
            angle_min = max(angle_min, lidar_angle_min)
            angle_max = min(angle_max, lidar_angle_max)

            range_low_index = int((angle_min - lidar_angle_min) / lidar_angle_increment)
            range_high_index = int((angle_max - lidar_angle_min) / lidar_angle_increment)

            desired_indices = np.arange(range_low_index,range_high_index+1)
            corresponding_angles = lidar_angle_min + desired_indices * lidar_angle_increment
            polar_coords = np.stack((lidar_ranges[range_low_index:range_high_index+1], corresponding_angles), axis=-1)

            # Distance Subset
            distance_mask = distance_min >= polar_coords[:,0] & polar_coords[:,0] <= distance_max
            polar_coords = polar_coords[distance_mask]

            cartesian_coords = self.polar_to_cartesian(polar_coords)

            return cartesian_coords

        return subset_calculator

    def polar_to_cartesian(self, polar_coords):
        """
        Returns a 2D array representing the polar form of a given array of cartesian points.

        Args:
            polar_coords (2D Array): an array of polar coordinates (r, theta)
                - examples:
                    - [(1, pi/4)]
                    - [(2, pi/3), (1, 0)]
        """
        return np.array([[r * np.cos(theta), r*np.sin(theta), 0.0, 1.0] for r,theta in polar_coords])

    def cartesian_to_polar(self, cart_coords):
        """
        Returns a 2D array representing the cartesian form of a given array of polar points.

        Args:
            cart_coords (2D Array): an array of cartesian coordinates (x, y)
                - examples:
                    - [(3, 5)]
                    - [(2, 8), (1, 2)]
        """
        return np.array([[np.sqrt(x**2 + y**2), np.arctan2(y/x)] for x,y in cart_coords])

    def points_dist_from_line(self, m, b, points):
        """
        Returns a 2D array representing the distance of a given array of points to a line

        Args:
            m (float): slope of the line
            b (float): y-intercept of the line
            points (2D Array): an array of cartesian points
                - examples:
                    - [(2,2)]
                    - [(1,3), (4,2)]
        """
        return np.array([[abs(m * x - y + b) / np.sqrt(m**2 + 1**2)] for x,y in points])

    def line_projection(self, velocity):
        """
        Returns the vector representing the projected location of base_link with respect to base_link.

        Parameters:
            - velocity (float): the current velocity of the drive command

        Output:
            - np array: 2d vector (x, y) of the end point of the projected line
        """
        projected_distance = self.SAFETY_CONTROLLER_CONST * velocity + self.SAFETY_RADIUS
        return np.array([projected_distance, 0]) # x direction is forward

    # TODO: Write your callback functions here

    def calculate_deltas(self, coords, line):
        """
        Takes in the lidar scan points in the desired range and calculates their
        distance to the line of our projected path for base_link.

        :param self: the Node
        :param coords: cartesian coords wrt to base_link of the scan
        :param line: vector to the projected location of base_link
        """
        deltas = np.dot(coords, line/np.linalg.norm(line))
        return deltas

    def drive_callback(self, drive_msg):
        """
        Based on a drive command, interrupt the drive command with a stop command
        if it would lead to a collision. Collision determined based on a point in
        the angle and distance range being too close to the projected path of the car

        :param self: safety controller node
        :param drive_msg: AckermanDriveStamped msg from other controllers
        """
        lidar_msg = self.lidar_msg
        # function to filter our laser data
        lidar_subset_calc = self.get_lidar_subset_calculator(
            lidar_msg.angle_min,
            lidar_msg.angle_max,
            lidar_msg.angle_increment,
            lidar_msg.ranges
        )

        # calculate the vector for our projected location
        velocity = drive_msg.speed
        line = self.line_projection(velocity)

        # filter laser scan to desired range
        cartesian_coords = lidar_subset_calc(
            angle_range = [-np.pi/4, np.pi/4],
            distance_range= [0,np.linalg.norm(line)]
        )

        # if any delta within the car safety radius, terminate the drive command
        deltas = self.calculate_deltas(cartesian_coords, line)
        mask = abs(deltas) < self.SAFETY_RADIUS
        filtered_cartesian = deltas[mask]

        if filtered_cartesian:
            self.publish_stop()

    def lidar_callback(self, lidar_msg):
        self.lidar_msg = lidar_msg

    def publish_stop(self):
        """
        Publishes a command for the car to stop
        """
        # https://docs.ros.org/en/jade/api/ackermann_msgs/html/msg/AckermannDriveStamped.html
        new_msg = AckermannDriveStamped()

        # https://docs.ros.org/en/jade/api/ackermann_msgs/html/msg/AckermannDrive.html
        drive_command = new_msg.drive
        drive_command.speed = 0.0
        drive_command.acceleration = 0.0
        # jerk indicates a desired absolute rate of acceleration change in either direction (increasing or decreasing).
        drive_command.jerk = 0.0

        self.stop_publisher.publish(new_msg)

def main():
    rclpy.init()
    safety_controller = SafetyController()
    rclpy.spin(safety_controller)
    safety_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
