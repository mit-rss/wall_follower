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
            # The robot is approximately a rectangle that stretches
            # - 0.2 meters forward
            # - 0.2 meters on each side
            # - 0.5 meters behind
            # We trigger the safety controller (which stops the car)
            # if we're within 0.2 meters within this bounding box.

            bounding_left = 0.4
            bounding_right = -0.4
            bounding_front = 0.4
            bounding_back = -0.7

            num_close_points = np.sum((ys < bounding_left) &
                                      (ys > bounding_right) &
                                      (xs < bounding_front) &
                                      (xs > bounding_back))
            
            
            # We only trigger if there are 5 or more points inside our bounding
            # box to avoid triggering due to noise
            if num_close_points < 5:
                print("#close points:", num_close_points)
                return
            
            print("Safety controller triggered!")
            self.drive_speed = 0.0
            drive = AckermannDriveStamped()
            drive.drive.speed = self.drive_speed
            drive.drive.steering_angle = np.clip(self.steering_angle, -0.34, 0.34)
	    print("changed steering angle:", drive.drive.steering_angle)	
            
	    #VisualizationTools.plot_line(dx, dy, self.line_pub, frame = "/laser")
	    #VisualizationTools.plot_line([closest_distance*np.sin(closest_ang), 0],[closest_distance*np.sin(closest_ang), 0], self.short_line, color=(0, 1, 0), frame = "/laser")
	    self.safety_publisher.publish(drive)
            
if __name__ == "__main__":
        rospy.init_node('safety_controller')
        safety_controller = SafetyController()
        rospy.spin()
