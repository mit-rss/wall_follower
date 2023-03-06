#!/usr/bin/env python2

import rospy
import math

from ackermann_msgs.msg import AckermannDriveStamped

from scan_subscriber import ScanListener

class SafetyController:
        DRIVE_TOPIC = "/vesc/high_level/ackermann_cmd_mux/output"
        SAFETY_OVERWRITE_TOPIC = "/vesc/low_level/ackermann_cmd_mux/input/safety"
        def __init__(self, run_on_callback=None):
            """
            run_on_callback: An optional function to run on callback in addition to our normal methods
            """
            self.drive_subscriber = rospy.Subscriber(self.DRIVE_TOPIC, AckermannDriveStamped, self.callback)
            self.safety_publisher = rospy.Publisher(self.SAFETY_OVERWRITE_TOPIC, AckermannDriveStamped, queue_size=10)
            self.scan_listener = ScanListener()

            
            self.drive_speed = 0.0
            self.steering_angle = 0.0
            self.run_on_callback = run_on_callback
                                        
        def callback(self, drive):
            self.drive_speed = drive.drive.speed
            self.steering_angle = drive.drive.steering_angle

            angles, ranges = self.scan_listener.angles, self.scan_listener.ranges
            danger_indexes = (angles < self.steering_angle + math.pi / 2) & (angles > self.steering_angle - math.pi / 2)
            closest_distance = min(ranges[danger_indexes])

            max_velocity = 0.1 * (closest_distance - 0.2)
            if max_velocity >= self.drive_speed:
                return
            self.drive_speed = max_velocity
            drive = AckermannDriveStamped()
            drive.drive.drive_speed = self.drive_speed
            drive.drive.steering_angle = self.steering_angle
            self.safety_publisher.publish(drive)
