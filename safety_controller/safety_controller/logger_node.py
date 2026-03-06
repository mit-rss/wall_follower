import rclpy
import random
from rclpy.node import Node

from std_msgs.msg import Float32
from sensor_msgs.msg import LaserScan
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

class WallFollowerLogger(Node):
# TODO: error metric: where we want it to stop - where it actually stopped
# TODO: publish error metric WRT to different velocities

    def __init__(self):
        super().__init__('')
        self.declare_parameters(namespace = '', parameters = [
            ('subscriber_topic', 'crash_points'),
        ])

        self.subscription = self.create_subscription(
            LaserScan,
            self.get_parameter('subscriber_topic').value,
            self.listener_callback,
            10)

        rclpy.get_shutdown_context().on_shutdown(self.on_shutdown_callback)

        self.obstacle_sizes = []
        self.avg_distances = []

    def on_shutdown_callback(self):
        self.get_logger().info("--- Node is shutting down. Saving a log of the run. ---")
        obstacle_time_axis = [0 + i for i in range(len(self.obstacle_sizes))]
        distance_time_axis = [0 + i for i in range(len(self.avg_distances))]

        fig1 = plt.figure()
        plt.plot(obstacle_time_axis,self.obstacle_sizes)
        plt.figure('Obstacle Sizes Over Time During the Run')
        plt.ylabel('Count of lidar points cluster')
        plt.xlable('Timestep')

        fig2 = plt.figure()
        plt.plot(distance_time_axis,self.avg_distances)
        plt.figure('Average Distance To Obstacles During the Run')
        plt.ylabel('Distance (m)')
        plt.xlable('Timestep')

        fig1.savefig('obstacle_count')
        fig2.savefig('avg_dist')
        fig1.close()
        fig2.close()

        obstacles_df = pd.DataFrame(self.obstacle_sizes)
        distances_df = pd.DataFrame(self.avg_distances)
        obstacles_df.to_csv('obstacle_count',index=False)
        distances_df.to_csv('avg_dist',index=False)
        self.get_logger().info(f'Saved csv files and plots to {os.getcwd()}/')

    def listener_callback(self, msg):
        points = msg.ranges

        n = len(points)
        if n > 0:
            self.get_logger().info(f'Currently detecting a crash of size: {n}')

        avg_distance = np.mean(np.array(n))

        self.obstacle_sizes.append(n)
        self.avg_distances.append(avg_distance)


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = WallFollowerLogger()

    rclpy.spin(minimal_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
