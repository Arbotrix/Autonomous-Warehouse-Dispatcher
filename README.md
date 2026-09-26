# Warehouse Delivery Robot (ROS 2 + Nav2 + Gazebo)

An autonomous mobile robot (AMR) simulation for warehouse patrol/delivery, built with **ROS 2 (Humble)**, **Nav2**, **Gazebo**, and **SLAM Toolbox / AMCL**. The robot maps a simulated warehouse environment, localizes within the saved map, and autonomously patrols between a set of predefined waypoints using Nav2's action-based navigation stack.

---

## 1. Overview

This project demonstrates a complete autonomous navigation pipeline:

1. **Simulation** — A custom warehouse world is simulated in Gazebo with a differential-drive robot equipped with a 2D LiDAR.
2. **Mapping** — The environment is mapped using `slam_toolbox` (live SLAM) while the robot is manually driven with teleop.
3. **Map Saving** — The generated occupancy grid map is saved to disk using `nav2_map_server`.
4. **Localization** — On subsequent runs, the saved map is loaded and the robot localizes itself within it using **AMCL**.
5. **Autonomous Patrol** — A Python script using Nav2's `BasicNavigator` (Simple Commander API) sends the robot to a set of randomly chosen waypoints in a continuous loop.

---

## 2. System Requirements

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic (11)
- Nav2 (`nav2_bringup`, `nav2_map_server`, `nav2_lifecycle_manager`, `nav2_simple_commander`)
- `slam_toolbox`
- `teleop_twist_keyboard`

Install missing dependencies:
```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-slam-toolbox ros-humble-teleop-twist-keyboard \
  ros-humble-nav2-simple-commander
```

---

## 3. Package Structure

```
warehouse_delivery_rbt/
├── CMakeLists.txt
├── package.xml
├── urdf/
│   └── delivery_robot.urdf        # Robot description
├── worlds/
│   └── warehouse.world            # Gazebo simulation world
├── config/
│   ├── nav2_params.yaml           # Nav2 stack parameters (costmaps, planner, controller, etc.)
│   └── warehouse.rviz             # RViz display configuration
├── maps/
│   ├── warehouse_map.yaml         # Saved map metadata (generated after mapping)
│   └── warehouse_map.pgm          # Saved occupancy grid image (generated after mapping)
├── launch/
│   ├── warehouse_launch.py             # SLAM (live mapping) launch file
│   └── warehouse_autonomous.launch.py  # Saved-map + AMCL launch file (for autonomous patrol)
└── scripts/
    └── warehouse_navigator.py     # Random-patrol autonomous navigation script
```

> **Important:** `CMakeLists.txt` must install the `maps` directory, or `map_server` will fail to find the saved map file at runtime:
> ```cmake
> install(DIRECTORY launch worlds urdf config maps
>   DESTINATION share/${PROJECT_NAME}
> )
> install(PROGRAMS scripts/warehouse_navigator.py
>   DESTINATION lib/${PROJECT_NAME}
> )
> ```

---

## 4. Building the Package

```bash
cd ~/arbotrix_ws
colcon build --packages-select warehouse_delivery_rbt
source install/setup.bash
```

Re-run this after **any** change to `CMakeLists.txt`, `launch/`, `config/`, or `maps/` — installed files live under `install/`, not `src/`.

---

## 5. Step-by-Step Usage

### Step 1 — Map the environment (first time only)

Launch Gazebo + live SLAM:
```bash
ros2 launch warehouse_delivery_rbt warehouse_launch.py
```

Drive the robot around the entire warehouse to build the map:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Tips for a precise map:**
- Drive slowly, especially through corners.
- Complete a full loop back to the starting point (loop closure) to correct drift.
- Pause briefly in open areas to gather more scan samples.
- Visually inspect the map in RViz before saving — walls should appear as single sharp lines, not blurry/doubled lines.

### Step 2 — Save the map

Once mapping is complete:
```bash
cd ~/arbotrix_ws/src/warehouse_delivery_rbt/maps
ros2 run nav2_map_server map_saver_cli -f warehouse_map
```

This creates `warehouse_map.yaml` and `warehouse_map.pgm` in the `maps/` folder. Rebuild the package afterward so the saved map is copied into the installed share directory:
```bash
cd ~/arbotrix_ws
colcon build --packages-select warehouse_delivery_rbt
source install/setup.bash
```

### Step 3 — Launch with the saved map (autonomous mode)

```bash
ros2 launch warehouse_delivery_rbt warehouse_autonomous.launch.py
```

This starts Gazebo, `map_server`, `AMCL`, the full Nav2 stack, and RViz, using the previously saved map instead of live SLAM.

### Step 4 — Set the initial pose

AMCL does not know the robot's starting position until told. In RViz:
1. Select the **"2D Pose Estimate"** tool.
2. Click-and-drag on the map at the robot's actual position/orientation in Gazebo (typically the origin, `(0, 0)`, matching the spawn point).

Confirm localization succeeded:
```bash
ros2 topic echo /amcl_pose --once
```
A low covariance and a reasonable pose confirms AMCL has localized correctly. In RViz, the laser scan (red dots) should align with the map's walls.

### Step 5 — Get real waypoint coordinates

Use RViz's **"Publish Point"** tool to record accurate, map-frame coordinates for each target location (do **not** guess coordinates from Gazebo's world view — they will not match the map frame).

```bash
ros2 topic echo /clicked_point
```
Click each target location in RViz; note the `x, y` values printed in the terminal.

### Step 6 — Update waypoints and run the patrol

Edit `scripts/warehouse_navigator.py` and update the `SAFE_POINTS` dictionary with the coordinates from Step 5:
```python
SAFE_POINTS = {
    "Point 1": (1.77, 2.07),
    "Point 2": (5.99, 4.11),
    "Point 3": (6.99, -2.04),
    "Point 4": (10.73, 1.40),
}
```

Run the patrol:
```bash
ros2 run warehouse_delivery_rbt warehouse_navigator.py
```

The robot will continuously navigate to randomly chosen waypoints from the list, waiting 3 seconds at each before selecting the next.

---

## 6. Key Nav2 Parameters (`config/nav2_params.yaml`)

| Node | Parameter | Value | Purpose |
|---|---|---|---|
| `controller_server` | `controller_frequency` | 20.0 | Target control loop rate (Hz) |
| `controller_server` (DWB) | `sim_time` | 1.7 | Trajectory simulation horizon (s) |
| `controller_server` (DWB) | `vx_samples`, `vy_samples`, `vtheta_samples` | 20 / 5 / 20 | Velocity sampling resolution |
| `global_costmap` / `local_costmap` | `inflation_layer.inflation_radius` | 0.55 | Obstacle inflation buffer (m) — reduce if the robot fails to reach goals near narrow aisles |
| `global_costmap` / `local_costmap` | `robot_radius` | 0.35 | Robot footprint radius (m) |
| `local_costmap` | `width`, `height` | 3 x 3 | Rolling local costmap size (m) |
| `planner_server` (GridBased) | `allow_unknown` | true | Allows planning through unmapped space |
| `velocity_smoother` | `velocity_timeout` | 1.0 | Zeroes output if no command received within this window (s) |
| `amcl` | `max_particles` / `min_particles` | 2000 / 500 | Particle filter size for localization |

Live tuning (no restart needed, resets on next launch):
```bash
ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.3
ros2 param set /local_costmap/local_costmap inflation_layer.inflation_radius 0.3
```

To reduce controller CPU load (useful on virtualized/low-resource machines) and lower the DWB trajectory sample count, edit `config/nav2_params.yaml` directly under `controller_server.FollowPath`:
```yaml
vx_samples: 10
vtheta_samples: 10
vy_samples: 1
```
Or apply the same edit from the command line and rebuild:
```bash
sed -i 's/vx_samples: 20/vx_samples: 10/' config/nav2_params.yaml
sed -i 's/vtheta_samples: 20/vtheta_samples: 10/' config/nav2_params.yaml
sed -i 's/vy_samples: 5/vy_samples: 1/' config/nav2_params.yaml
colcon build --packages-select warehouse_delivery_rbt
```

---

## 7. Troubleshooting

**Robot reports "Success" almost instantly but never actually moves in Gazebo:**
Usually caused by leftover/ghost ROS 2 nodes from a previous crashed session interfering with discovery. Fully restart the system (or at minimum kill all Gazebo/Nav2 processes and restart the ROS 2 daemon) before relaunching:
```bash
pkill -9 -f gazebo
pkill -9 -f rviz2
pkill -9 -f nav2
ros2 daemon stop && ros2 daemon start
```

**`ros2 lifecycle get /velocity_smoother` (or `/map_server`, `/amcl`) shows `unconfigured`:**
The `lifecycle_manager` did not autostart it. Manually configure/activate for a quick check:
```bash
ros2 lifecycle set /velocity_smoother configure
ros2 lifecycle set /velocity_smoother activate
```
If this fixes it, ensure a proper restart is done afterward rather than relying on manual activation long-term.

**RViz shows "Frame [map] does not exist":**
`AMCL`/`map_server` hasn't published yet, or no initial pose has been set. Set the "2D Pose Estimate" in RViz.

**RViz Map display shows "No map received" even though `/map` is publishing data:**
QoS mismatch — `map_server` publishes with `Transient Local` durability, but RViz's Map display may default to `Volatile`. In the Displays panel, expand **Map → Durability Policy** and change it to `Transient Local`.

**`map_server` fails to configure / lifecycle transition fails:**
The saved map file isn't present in the installed share directory. Confirm the `maps` folder is listed in `CMakeLists.txt`'s `install(DIRECTORY ...)` and rebuild.

**Planner repeatedly logs `GridBased: failed to create plan` / `Pose Goes Off Grid`:**
The target coordinate is outside the mapped/known area, or inside an obstacle's inflation zone. Re-verify the coordinate using RViz's "Publish Point" tool on the actual saved map (not guessed from Gazebo).

**Robot moves one step then collides with a wall:**
The path may pass too close to obstacles for the current `inflation_radius`/`robot_radius` margin, especially in narrow aisles. Lower `inflation_radius` slightly, or choose waypoints further from shelves.

**Never call `navigator.lifecycleShutdown()` in a script that only needs to run once:**
This call deactivates the *entire* Nav2 stack (controller, planner, behavior server, velocity smoother, etc.), not just the script's local objects. Only call `rclpy.shutdown()` at the end of single-run scripts.

---

## 8. Project Notes

- Live SLAM (`slam_toolbox`) rebuilds the map from scratch on every launch — it does not persist between sessions. Use the saved-map + AMCL workflow (`warehouse_autonomous.launch.py`) for repeatable testing.
- Waypoint coordinates must always be obtained in the **map frame** via RViz's "Publish Point" tool — coordinates read from Gazebo's world view will not match the map frame's origin/orientation.

---

## 9. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
