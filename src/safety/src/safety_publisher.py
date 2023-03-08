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
            print(angles, ranges)
            print("steering angle:", self.steering_angle)
            
            danger_indexes = (angles < self.steering_angle + math.pi / 4) & (angles > self.steering_angle - math.pi / 4)
	    danger_ranges = ranges[danger_indexes]
	    danger_angles = angles[danger_indexes]
	    dx, dy = danger_ranges*np.cos(danger_angles), danger_ranges*np.sin(danger_angles)
            print("danger indexes:", danger_indexes)
	    print(min(ranges))
	    closest_ind = min(range(len(danger_ranges)), key= lambda x: danger_ranges[x])
	    closest_ang = danger_angles[closest_ind]
            closest_distance = danger_ranges[closest_ind]#min(ranges[danger_indexes])
            print("closest distance:", closest_distance)
            max_velocity = 10 * (closest_distance - 0.2)
            print("max velocity:", max_velocity)
            if max_velocity >= self.drive_speed:
                print("Safe speed")
                return
            print("Slow down!")
            self.drive_speed = max(0.0, max_velocity)
            drive = AckermannDriveStamped()
            drive.drive.speed = self.drive_speed
            drive.drive.steering_angle = np.clip(self.steering_angle, -0.34, 0.34)
	    print("changed steering angle:", drive.drive.steering_angle)	
            
	    VisualizationTools.plot_line(dx, dy, self.line_pub, frame = "/laser")
	    VisualizationTools.plot_line([closest_distance*np.sin(closest_ang), 0],[closest_distance*np.sin(closest_ang), 0], self.short_line, color=(0, 1, 0), frame = "/laser")
	    self.safety_publisher.publish(drive)
            
if __name__ == "__main__":
        rospy.init_node('safety_controller')
        safety_controller = SafetyController()
        rospy.spin()
