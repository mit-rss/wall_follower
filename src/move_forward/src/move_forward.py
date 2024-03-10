#!/usr/bin/env python2
import rospy
from ackermann_msgs.msg import AckermannDriveStamped


class MoveForward:
    # Import ROS parameters from the "params.yaml" file.
    # Access these variables in class functions with self:
    # i.e. self.CONSTANT
    DRIVE_TOPIC = rospy.get_param("move_forward/drive_topic")
    VELOCITY = rospy.get_param("move_forward/velocity")

    def __init__(self):
        self.pub = rospy.Publisher(self.DRIVE_TOPIC, AckermannDriveStamped)
        self.rate = rospy.Rate(20)


    def run(self):
        while not rospy.is_shutdown():
            ack_msg = AckermannDriveStamped()
            ack_msg.drive.steering_angle = 0.0
            ack_msg.drive.speed = self.VELOCITY
            self.pub.publish(ack_msg)
            self.rate.sleep()

if __name__ == "__main__":
    rospy.init_node('move_forward')
    wall_follower = WallFollower()
    wall_follower.run()
