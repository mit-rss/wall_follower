#!/usr/bin/env python2

import rospy
import math

from ackermann_msgs.msg import AckermannDriveStamped

from scan_subscriber import ScanListener

class SafetyController:
        DRIVE_TOPIC = "/vesc/high_level/ackermann_cmd_mux/output"
        SAFETY_OVERWRITE_TOPIC = "/vesc/low_level/ackermann_cmd_mux/input/safety"
        def __init__(self):
            self.drive_subscriber = rospy.Subscriber(self.DRIVE_TOPIC, AckermannDriveStamped, self.callback)
            self.safety_publisher = rospy.Publisher(self.SAFETY_OVERWRITE_TOPIC, AckermannDriveStamped, queue_size=10)
            self.scan_listener = ScanListener()

            
            self.drive_speed = 0.0
            self.steering_angle = 0.0
                                        
        def callback(self, drive):
            self.drive_speed = drive.drive.speed
            self.steering_angle = drive.drive.steering_angle

            angles, ranges = self.scan_listener.angles, self.scan_listener.ranges
            print(angles, ranges)
            print(self.steering_angle)
            danger_indexes = (angles < self.steering_angle + math.pi / 4) & (angles > self.steering_angle - math.pi / 4)
            print(min(ranges))
            closest_distance = min(ranges[danger_indexes])
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
            drive.drive.steering_angle = self.steering_angle
            self.safety_publisher.publish(drive)
            
if __name__ == "__main__":
        rospy.init_node('safety_controller')
        safety_controller = SafetyController()
        rospy.spin()
