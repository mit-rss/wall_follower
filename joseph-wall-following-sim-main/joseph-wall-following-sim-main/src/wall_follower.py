#!/usr/bin/env python2

import numpy as np

import rospy
from rospy.numpy_msg import numpy_msg
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive
from visualization_tools import *

def normalize_angle(angle):
    angle = angle % (2 * np.pi)
    if angle > np.pi:
        angle -= 2 * np.pi
    return angle


class WallFollower:
    # Import ROS parameters from the "params.yaml" file.
    # Access these variables in class functions with self:
    # i.e. self.CONSTANT
    SCAN_TOPIC = rospy.get_param("wall_follower/scan_topic")
    DRIVE_TOPIC = rospy.get_param("wall_follower/drive_topic")
    SIDE = rospy.get_param("wall_follower/side")
    VELOCITY = rospy.get_param("wall_follower/velocity")
    DESIRED_DISTANCE = rospy.get_param("wall_follower/desired_distance")
    MAX_VELOCITY = rospy.get_param("racecar_simulator/max_speed")
    MAX_STEERING_ANGLE = rospy.get_param("racecar_simulator/max_steering_angle")
    
    def __init__(self):
        # TODO:
        # Initialize your publishers and
        # subscribers here
        self.scan_subscriber = rospy.Subscriber(self.SCAN_TOPIC, numpy_msg(LaserScan), self.laser_callback)

        self.drive_publisher = rospy.Publisher(self.DRIVE_TOPIC, AckermannDriveStamped, queue_size=1)
        self.rate = rospy.Rate(10.0) # 10 Hz

        self.wall_angle = 0.0
        self.wall_distance = 1.0
        self.desired_angle = normalize_angle(np.pi / 2 * self.SIDE)
        self.desired_distance = self.DESIRED_DISTANCE
        self.desired_velocity = self.VELOCITY
        self.speed = 1.0
        self.accumulated_error = 0.0
        self.line_publisher = rospy.Publisher("/visualization_marker", Marker, queue_size=1)
        
    def laser_callback(self, laser_scan):

        # Adjust my predicted distance to the wall based on the laser scan

        # Find the closest point on the LIDAR scan. This is an estimate
        # of where the closest wall is
        angles = np.linspace(laser_scan.angle_min, laser_scan.angle_max, len(laser_scan.ranges))
        ranges = np.array(laser_scan.ranges)
        if (self.SIDE > 0):
            ranges2 = ranges + 10 * (angles < 0)
        else:
            ranges2 = ranges + 10 * (angles > 0)
        i = np.argmin(ranges2)
        #rospy.logwarn(ranges)
        #rospy.logwarn(ranges2)
        #rospy.logwarn("\n\n")
        selected_indexes = (ranges2 < ranges[i] + 1)
        angles, ranges = angles[selected_indexes], ranges[selected_indexes]
        xs, ys = ranges * np.cos(angles), ranges * np.sin(angles)
        
        def get_close_points(x, y, percentile=50):
            """
            Returns the indexes of the 50% closest points to the line with
            closest point (x, y)
            """
            dists = np.abs(x * xs + y * ys - (x * x + y * y))
            p = np.percentile(dists, percentile)
            return dists <= p
            
        i = np.argmin(ranges)
        r, theta = ranges[i], angles[i]
        x, y = r * np.cos(theta), r * np.sin(theta)
        x, y = 0, 0


        # I was implementing RANSAC, but RANSAC doesn't
        # work with corners as well as a simple linear regression
        # so I just have it doing it once right now :)
        for _ in range(1):
            close_points = get_close_points(x, y)
            xs_, ys_ = xs[close_points], ys[close_points]
            A = np.column_stack((xs_, ys_))
            b = np.ones((len(xs_), 1))
            x, y = np.linalg.lstsq(A, b)[0]
            distance = 1 / (x ** 2 + y ** 2) ** 0.5
            x, y = x * distance ** 2, y * distance ** 2

        VisualizationTools.plot_line(xs_, ys_, self.line_publisher)
        
        angle = np.arctan2(y, x)
        distance = 1 / (x ** 2 + y ** 2) ** 0.5
        x, y = x * distance ** 2, y * distance ** 2
        self.wall_angle = angle
        self.wall_distance = 1 / distance
    
    def run(self):
        # Basically, the main loop
        while not rospy.is_shutdown():
            self.drive_publisher.publish(self._get_drive())
            self.rate.sleep()

    def _get_steering_angle(self):
        """Return what direction we should be steering the car"""
        # First off, we should always be in the range between pointing
        # directly at the wall and pointing directly away from the wall.
        # If we're not in this range, we should steer as fast as we can
        # towards it.

        angle_diff = normalize_angle(self.desired_angle - self.wall_angle)
        if angle_diff < -np.pi / 2:
            # We should rotate left
            return self.MAX_STEERING_ANGLE
        if angle_diff > np.pi / 2:
            # We should rotate right
            return -self.MAX_STEERING_ANGLE
        
        # Now do finer control
        distance_diff = self.SIDE * (self.wall_distance - self.desired_distance)
        distance_derivative = -self.speed * np.sin(angle_diff)# * self.SIDE
        self.accumulated_error += distance_diff * 0.03
        if self.accumulated_error > 0.5:
            self.accumulated_error = 0.5
        if self.accumulated_error < -0.5:
            self.accumulated_error = -0.5
        
        K = 0.5
        KD = 0.35
        KI = 0.25
        
        alpha = distance_diff * K + distance_derivative * KD + self.accumulated_error * KI
        if alpha < -self.MAX_STEERING_ANGLE:
            alpha = -self.MAX_STEERING_ANGLE
        if alpha > self.MAX_STEERING_ANGLE:
            alpha = self.MAX_STEERING_ANGLE
        return alpha
       
    def _get_drive_speed(self):
        """Return how fast we should be driving the car"""
        self.speed = self.VELOCITY
        return self.speed
    
    def _get_drive(self):
        """
        Return an AckermannDriveStamped corresponding to how you want to
        drive the robot
        """

        steering_angle = self._get_steering_angle()
        drive_speed = self._get_drive_speed()
        
        drive = AckermannDriveStamped()
        drive.drive.steering_angle = steering_angle
        drive.drive.speed = drive_speed
        return drive

if __name__ == "__main__":
    rospy.init_node('wall_follower')
    wall_follower = WallFollower()
    wall_follower.run()
