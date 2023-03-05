#!/usr/bin/env python2

import numpy as np

import rospy
from rospy.numpy_msg import numpy_msg
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped

class ScanSubscriber:
    SCAN_TOPIC = "/scan" # rospy.get_param("wall_follower/scan_topic")
    def __init__(self):
        self.subscriber = rospy.Subscriber(SCAN_TOPIC, numpy_msg(LaserScan), self.callback) 
    
    def callback(self, msg):
        angle_min = msg.angle_min
        angle_max = msg.angle_max
        angle_increment = msg.angle_increment
        ranges = msg.ranges

if __name__ == "__main__":
    rospy.init_node('scan_subscriber')
    scan_subscriber = ScanSubscriber()
    rospy.spin()

