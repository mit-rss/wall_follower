import rospy

from ackermann_msgs.msg import AckermannDriveStamped


class OutputListener:
    OUTPUT_TOPIC = "/vesc/high_level/ackermann_cmd_mux/output"
    def __init__(self,):
        self.output_subscriber = rospy.Subscriber(self.OUTPUT_TOPIC, AckermannDriveStamped, self.callback)

        self.drive_speed = 0.0
        self.steering_angle = 0.0

    def callback(self, drive):
        self.drive_speed = drive.drive.speed
        self.steering_angle = drive.drive.steering_angle
