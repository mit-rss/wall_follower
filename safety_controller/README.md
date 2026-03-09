Safety_controller subscribes to ouster_points and imu_packets.
First, projects car's position in the next 1 second.
Second, takes the linear regression between curr position and future position.
Third, calculates distance from lidar points to line. If within crash delta (.2 m), then publishes STOP command.
