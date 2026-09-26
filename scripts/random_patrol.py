#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import time
import random
import sys

# ---> REPLACE THESE WITH YOUR REAL RVIZ FLOOR COORDINATES <---
SAFE_POINTS = {
    "Point 1 (Near Orange)": (3.5, -1.5),
    "Point 2 (Near Red)": (6.0, -3.5),
    "Point 3 (Near Green)": (9.5, 3.0),
    "Point 4 (Near Yellow)": (10.0, -3.5),
    "Point 5 (Hallway Center)": (4.0, 5.0)
}

def create_pose(nav, x, y):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.orientation.w = 1.0
    return pose

def main():
    sys.argv.extend(['--ros-args', '-p', 'use_sim_time:=true'])
    rclpy.init(args=sys.argv)
    navigator = BasicNavigator()
    
    print("Connecting to Nav2 Action Server...")
    navigator.nav_to_pose_client.wait_for_server()
    time.sleep(2.0)
    print("Clearing costmaps...")
    navigator.clearAllCostmaps()
    time.sleep(1.0)
    print("Nav2 is ready! Starting Random Patrol...")

    while rclpy.ok():
        # 1. Randomly pick a destination from our safe list
        name, coords = random.choice(list(SAFE_POINTS.items()))
        goal_pose = create_pose(navigator, coords[0], coords[1])
        
        print(f"\n--- New Random Target: {name} at X:{coords[0]}, Y:{coords[1]} ---")
        navigator.goToPose(goal_pose)

        # 2. Wait for the robot to arrive (with CPU safety sleep)
        while not navigator.isTaskComplete():
            time.sleep(0.1)

        # 3. Check if it worked, wait 3 seconds, then repeat!
        if navigator.getResult() == TaskResult.SUCCEEDED:
            print(f"Success! Arrived at {name}. Waiting 3 seconds...")
            time.sleep(3.0)
        else:
            print(f"Failed to reach {name}. Trying a new random point...")
            navigator.clearAllCostmaps()
            time.sleep(2.0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nPatrol stopped by user.")
