import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped
from visualization_msgs.msg import Marker

from safety_controller.visualization_tools import VisualizationTools

class SafetyController(Node):

    def __init__(self):
        super().__init__("safety_controller")
        # Declare parameters to make them available for use
        # DO NOT MODIFY THIS!
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("drive_topic_listen", "/vesc/low_level/ackermann_cmd") # publish to the highest priority to override other drive commands
        self.declare_parameter('drive_topic_publish', "/vesc/low_level/input/safety")
        self.declare_parameter("safety_radius", 0.5)
        self.declare_parameter("safety_controller_const", 0.25)
        self.declare_parameter("logger_topic", "/crash_points")
        
        # Fetch constants from the ROS parameter server
        # DO NOT MODIFY THIS! This is necessary for the tests to be able to test varying parameters!
        self.SCAN_TOPIC = self.get_parameter('scan_topic').get_parameter_value().string_value
        self.DRIVE_TOPIC_LISTEN = self.get_parameter('drive_topic_listen').get_parameter_value().string_value
        self.DRIVE_TOPIC_PUBLISH = self.get_parameter('drive_topic_publish').get_parameter_value().string_value
        self.SAFETY_RADIUS = self.get_parameter('safety_radius').get_parameter_value().double_value
        self.SAFETY_CONTROLLER_CONST = self.get_parameter('safety_controller_const').get_parameter_value().double_value
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

        self.line_publisher = self.create_publisher(
            Marker,
            "line",
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
    
    # TODO: Write your callback functions here

    def drive_callback(self, drive_msg):
        """
        Based on a drive command, interrupt the drive command with a stop command
        if it would lead to a collision. Collision determined based on a point in
        the angle and distance range being too close to the projected path of the car

        Args:
            - drive_msg (AckermannDriveStamped): AckermanDriveStamped msg from other controllers
        """
        lidar_msg = self.lidar_msg
        if lidar_msg is None: return
        self.get_logger().info(f'{len(lidar_msg.ranges)}')
        # function to filter our laser data
        lidar_subset_calc = self.get_lidar_subset_calculator(
            lidar_msg.angle_min,
            lidar_msg.angle_max,
            lidar_msg.angle_increment,
            lidar_msg.ranges
        )

        # calculate the vector for our projected location
        velocity = drive_msg.drive.speed
        line = self.line_projection(velocity)
        
        # visualize the projected path to location in RViz
        self.visualize_line(line)

        # filter laser scan to desired range
        cartesian_coords = lidar_subset_calc(
            angle_range = [-np.pi/4, np.pi/4],
            distance_range= [0,np.linalg.norm(line)]
        )
        # PROBLEM: this is giving us absolutely nothing

        # if any delta within the car safety radius, terminate the drive command
        deltas = self.calculate_deltas(cartesian_coords, line)
        self.get_logger().info(f'pre-masked deltas: {len(deltas)}')
        mask = abs(deltas) < self.SAFETY_RADIUS
        filtered_cartesian = deltas[mask]
        self.get_logger().info(f'Deltas: {filtered_cartesian}')
        if len(filtered_cartesian) > 0:
            self.publish_stop()

    def lidar_callback(self, lidar_msg):
        self.lidar_msg = lidar_msg

    def publish_stop(self):
        """
        Publishes a command for the car to stop.
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
        
    def get_lidar_subset_calculator(self, lidar_angle_min, lidar_angle_max, lidar_angle_increment, lidar_ranges):
        """
        Returns a function tuned to the lidar's base parameters (lidar_angle_min, lidar_angle_max, and lidar_angle_increment)
        that returns points within an angle range.

        Args:
            - lidar_angle_min (float): The minimum angle supported by the lidar
            - lidar_angle_max (float): The maximum angle supported by the lidar
            - lidar_angle_increment (float): The size of the increments in the range [lidar_angle_min, lidar_angle_max]
            - lidar_ranges (array): The original lidar data, an indexed by angle with values corresponding to the distance of the point
            from the lidar
        """
        def subset_calculator(angle_range = [lidar_angle_min, lidar_angle_max], distance_range = [0, float("inf")]):
            """
            Returns the cartesian coordinates of the lidar points within a given range of angles
            and a given distance range.

            Args:
                angle_range (array): The given range of angles
                distance_range (array): The given range of distance
            """
            angle_min, angle_max = angle_range
            distance_min, distance_max = distance_range

            # Angle Subset
            if angle_min > angle_max:
                # Swap angles if given in wrong order
                angle_min, angle_max = angle_max, angle_min

            # Clip angles to the minimum and maximum angles supported by the lidar
            angle_min = max(angle_min, lidar_angle_min)
            angle_max = min(angle_max, lidar_angle_max)

            # Compute the range indices associated with the minumum and maximum angle 
            range_low_index = int((angle_min - lidar_angle_min) / lidar_angle_increment)
            range_high_index = int((angle_max - lidar_angle_min) / lidar_angle_increment)

            # Create array of indices associated with each value in our valid range
            desired_indices = np.arange(range_low_index,range_high_index+1)
            # Scale to increment based on given value, giving us each angle
            corresponding_angles = lidar_angle_min + desired_indices * lidar_angle_increment
            # Use the min and max index values to clip ranges to valid points
            corresponding_ranges = np.array(lidar_ranges[range_low_index:range_high_index+1], dtype="float32")
            
            # Distance mask to filter out points outside given range
            distance_mask = (distance_min <= corresponding_ranges) & (corresponding_ranges <= distance_max)
            
            # Apply distance mask to angles
            valid_angles = corresponding_angles[distance_mask]
            # Apply distance mask to ranges
            valid_ranges = corresponding_ranges[distance_mask]
            
            # Convert valid points to Cartesian coordinates
            x = valid_ranges * np.cos(valid_angles)
            y = valid_ranges * np.sin(valid_angles)
            
            # Stack Cartestian coordinates together and transpose
            cartesian_coords = np.vstack((x, y)).T # Shape: (num_points, 2)
            
            return cartesian_coords

        return subset_calculator
    
    def visualize_line(self, line_end_point):
        end_x, end_y = line_end_point
        VisualizationTools.plot_line(
            x = [0, end_x],
            y = [0, end_y],
            publisher = self.line_publisher,
        )
        
    def line_projection(self, velocity):
        """
        Returns the vector representing the projected location of base_link with respect to base_link.

        Args:
            - velocity (float) : the current velocity of the drive command

        Output:
            - line (ndarray): (1, 2) 2d vector (x, y) of the end point of the projected line.
        """
        projected_distance = self.SAFETY_CONTROLLER_CONST * velocity + self.SAFETY_RADIUS
        line = np.array([projected_distance, 0]) # x direction is forward
        return line
    
    def calculate_deltas(self, coords, line):
        """
        Takes in the lidar scan points in the desired range and calculates their
        distance to the line of our projected path for base_link.

        Args:
            - coords (ndarray): (num_points, 2) Cartesian coordinates of each scan point w.r.t. base link. 
            - line (ndarray) : (1, 2) Vector to the projected location of base_link.
        """
        self.get_logger().info(f'calculate_deltas input: {len(coords)}')
        
        # Calculate the unit vector associated with the line
        unit_vec = line/np.linalg.norm(line)
        
        # Calculate the cross product between each coordinate and the unit vector
        # This gets distances to the projected path line
        deltas = np.cross(coords, unit_vec)
        
        # Return distances to projected path line
        return deltas

def main():
    rclpy.init()
    safety_controller = SafetyController()
    rclpy.spin(safety_controller)
    safety_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
