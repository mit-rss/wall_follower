#!/usr/bin/env python2

import rospy
import math
import numpy as np

from ackermann_msgs.msg import AckermannDriveStamped

from scan_subscriber import ScanListener
from visualization_tools import *

class SafetyController:
        DRIVE_TOPIC = "/vesc/high_level/ackermann_cmd_mux/output"
        SAFETY_OVERWRITE_TOPIC = "/vesc/low_level/ackermann_cmd_mux/input/safety"

	line_topic = "/wall"
	shortest_topic = "/short"

        def __init__(self):
            self.drive_subscriber = rospy.Subscriber(self.DRIVE_TOPIC, AckermannDriveStamped, self.callback)
            self.safety_publisher = rospy.Publisher(self.SAFETY_OVERWRITE_TOPIC, AckermannDriveStamped, queue_size=10)
            self.scan_listener = ScanListener()
	   
	    #visualization markers
	    self.line_pub = rospy.Publisher(self.line_topic, Marker, queue_size = 1)
	    self.short_line = rospy.Publisher(self.shortest_topic, Marker, queue_size = 1)
            
            self.drive_speed = 0.0
            self.steering_angle = 0.0
                                      
        def callback(self, drive):
            self.drive_speed = drive.drive.speed
            self.steering_angle = drive.drive.steering_angle

            angles, ranges = self.scan_listener.angles, self.scan_listener.ranges
            xs, ys = ranges * np.cos(angles), ranges * np.sin(angles)
            """
	    The robot is approximately a rectangle that stretches
             - 0.2 meters forward
             - 0.15 meters on each side
             - 0.4 meters behind
	    There's two cases to consider:
	    1. If the robot is moving forward, then trigger if there are too many points
	       in a box near the front.
	    2. If the robot is moving backward, then trigger if there are too many points
	       in a box near the back.
	    In particular, I take a 0.6 meter wide box around the front/back of the car to consider
	    points in. (It also stretches 0.2 meters in front of/behind the car, and to the center of the
	    LIDAR sensor)
	    """

            if self.drive_speed > 0:
		# We're moving forward
		bounding_front = 0.3
		bounding_left = 0.2
		bounding_right = -0.2
		bounding_back = 0.0
                
                slow_bound_left = 0.3
                slow_bound_right = -0.3
                slow_bound_front = 0.5
                slow_bound_back = 0.0
	    else:
		# We're moving backward
		bounding_front = 0.0
		bounding_left = 0.2
		bounding_right = -0.2
		bounding_back = -0.4

                slow_bound_left = 0.3
                slow_bound_right = -0.3
                slow_bound_front = 0.0
                slow_bound_back = -0.6

            num_close_points = np.sum((ys < slow_bound_left) &
                                      (ys > slow_bound_right) &
                                      (xs < slow_bound_front) &
                                      (xs > slow_bound_back))
            

            num_danger_points = np.sum((ys < bounding_left) &
                                      (ys > bounding_right) &
                                      (xs < bounding_front) &
                                      (xs > bounding_back))
                        
            # We only trigger if there are 5 or more points inside our bounding
            # box to avoid triggering due to noise
            if num_close_points < 5:
                return

            if num_danger_points >= 5:
                print("Safety controller triggered: In danger zone! Stop now!")
                self.drive_speed = 0.0
                drive = AckermannDriveStamped()
                drive.drive.speed = self.drive_speed
            else:
                print("Safety controller triggered: In slow zone! Slowing down.")
                self.drive_speed = 0.5 * np.sign(self.drive_speed)
                drive = AckermannDriveStamped()
                drive.drive.speed = self.drive_speed
            drive.drive.steering_angle = self.steering_angle
            
	    #VisualizationTools.plot_line(dx, dy, self.line_pub, frame = "/laser")
	    #VisualizationTools.plot_line([closest_distance*np.sin(closest_ang), 0],[closest_distance*np.sin(closest_ang), 0], self.short_line, color=(0, 1, 0), frame = "/laser")
	    self.safety_publisher.publish(drive)
            
if __name__ == "__main__":
        rospy.init_node('safety_controller')
        safety_controller = SafetyController()
        rospy.spin()
