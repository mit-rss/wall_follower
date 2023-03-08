#!/usr/bin/env python2

import rospy

import numpy as np
from rospy.numpy_msg import numpy_msg
from sensor_msgs.msg import LaserScan


class ScanListener:
    SCAN_TOPIC = "/scan"
    def __init__(self, run_on_callback=None):
        """
        run_on_callback: An optional function to run on callback.
        """

        self.scan_subscriber = rospy.Subscriber(self.SCAN_TOPIC, LaserScan, self.callback)

        self.angles = []
        self.ranges = []
	self.run_on_callback = run_on_callback

    def callback(self, lidar_scan):
        self.angles = np.linspace(lidar_scan.angle_min, lidar_scan.angle_max, len(lidar_scan.ranges))
        self.ranges = np.array(lidar_scan.ranges)
	if self.run_on_callback is not None:
            self.run_on_callback()
        
if __name__ == '__main__':
    try:
        ScanListener()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass 
