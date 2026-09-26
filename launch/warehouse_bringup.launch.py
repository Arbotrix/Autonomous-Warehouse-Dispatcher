from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_dir = get_package_share_directory('warehouse_delivery_rbt')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    slam_toolbox_dir = get_package_share_directory('slam_toolbox')

    urdf = os.path.join(pkg_dir, 'urdf', 'delivery_robot.urdf')
    world = os.path.join(pkg_dir, 'worlds', 'warehouse.world')
    nav2_params = os.path.join(pkg_dir, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(pkg_dir, 'config', 'warehouse.rviz')

    # Get the default SLAM config path
    slam_config = os.path.join(slam_toolbox_dir, 'config', 'mapper_params_online_async.yaml')

    return LaunchDescription([
        ExecuteProcess(cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world], output='screen'),
        Node(package='robot_state_publisher', executable='robot_state_publisher', output='screen', arguments=[urdf], parameters=[{'use_sim_time': True}]),
        Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'delivery_robot', '-file', urdf, '-x', '0', '-y', '0', '-z', '0.1'], output='screen'),

        # FIX: Run SLAM Toolbox directly so we can forcefully inject the simulation clock!
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                slam_config,
                {'use_sim_time': True}
            ]
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')),
            launch_arguments={'use_sim_time': 'true', 'params_file': nav2_params}.items()
        ),

        # EXPLICIT lifecycle manager: guarantees velocity_smoother (and everything
        # else) is actually configured + activated on startup, regardless of what
        # navigation_launch.py's own internal lifecycle_manager does/doesn't include.
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': [
                    'controller_server',
                    'smoother_server',
                    'planner_server',
                    'behavior_server',
                    'velocity_smoother',
                    'bt_navigator',
                    'waypoint_follower'
                ]
            }]
        ),

        Node(package='rviz2', executable='rviz2', name='rviz2', output='screen', arguments=['-d', rviz_config], parameters=[{'use_sim_time': True}])
    ])
