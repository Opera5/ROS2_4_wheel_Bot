# Testbot — ROS 2 Navigation & Simulation Package

Testbot is a ROS 2 (Humble) differential-drive robot package built for autonomous navigation in simulation. It integrates Gazebo Fortress (Ignition), Nav2, SLAM Toolbox, AMCL, and `ros2_control` for a full navigation stack — from mapping to localization to goal-based path planning.

### Note: Change the Folder name to testbot(package name) or edit xm and CMakelist accordingly before building
---

## Table of Contents

- [Requirements](#requirements)
- [Package Structure](#package-structure)
- [Installation & Build](#installation--build)
- [Usage](#usage)
  - [1. Simulation Only (Gazebo + RViz)](#1-simulation-only-gazebo--rviz)
  - [2. SLAM Mapping](#2-slam-mapping)
  - [3. SLAM Localization (on saved map)](#3-slam-localization-on-saved-map)
  - [4. AMCL Localization (standalone)](#4-amcl-localization-standalone)
  - [5. Full Navigation (Nav2 + AMCL)](#5-full-navigation-nav2--amcl)
  - [6. Saving a Map](#6-saving-a-map)
- [Configuration Files](#configuration-files)
- [Key Components](#key-components)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Requirements

| Dependency | Version |
|---|---|
| ROS 2 | Humble |
| Gazebo | Fortress (Ignition) |
| Nav2 | Humble |
| SLAM Toolbox | Humble |
| ros2_control | Humble |
| robot_localization | Humble |
| topic_tools | Humble |
| twist_mux | Humble |

Install all ROS 2 dependencies:

```bash
cd ~/botdev
rosdep install --from-paths src --ignore-src -r -y
```

---

## Package Structure

```
testbot/
├── config/
│   ├── nav.yaml                  # Nav2 full stack parameters (costmaps, planner, controller)
│   ├── amcloc.yaml               # AMCL localization parameters
│   ├── slam_map.yaml             # SLAM Toolbox mapping parameters
│   ├── slam_loc.yaml             # SLAM Toolbox localization parameters
│   ├── ekf.yaml                  # robot_localization EKF parameters
│   ├── twistmux.yaml             # Twist multiplexer configuration
│   └── 4w_diff_drive_controller_velocity.yaml  # ros2_control diff drive config
├── description/
│   └── 4w_testbot.xacro          # Main robot URDF/Xacro model
├── launch/
│   ├── 4w_rsp.launch.py          # Core launch: Gazebo, RSP, EKF, bridges, controllers
│   ├── slamap.launch.py          # SLAM mapping mode
│   ├── slamloc.launch.py         # SLAM localization mode (on existing map)
│   ├── amcloc.launch.py          # Standalone AMCL localization
│   └── nav.launch.py             # Full Nav2 navigation (AMCL + Nav2 + RViz)
├── maps/
│   ├── testv1.yaml / testv1.pgm  # Default navigation map
│   ├── testhus_map.yaml / .pgm   # Husarion world map
│   └── v2.yaml / v2.pgm          # Alternative map
├── rviz/
│   ├── nav.rviz                  # Navigation RViz config (Nav2 + costmaps)
│   ├── async_map.rviz            # SLAM mapping RViz config
│   └── amcl.rviz                 # AMCL localization RViz config
└── worlds/
    └── husarion_world.sdf        # Husarion simulation world
```

---

## Installation & Build

```bash
# Clone into your workspace (if not already present)
cd ~/botdev/src

# Build the package
cd ~/botdev
colcon build --packages-select testbot --symlink-install

# Source the workspace
source install/setup.bash
```

> Use `--symlink-install` during development so changes to launch files, configs, and RViz files take effect without rebuilding.

---

## Usage

All launch commands assume you have sourced your workspace:

```bash
source ~/botdev/install/setup.bash
```

---

### 1. Simulation Only (Gazebo + RViz)

Launches Gazebo Fortress with the robot, `robot_state_publisher`, EKF, ros2_control, and sensor bridges. No navigation stack.

```bash
ros2 launch testbot 4w_rsp.launch.py
```

Optional arguments:

| Argument | Default | Description |
|---|---|---|
| `use_sim_time` | `true` | Use Gazebo simulation clock |
| `use_rviz` | `true` | Launch RViz |
| `run_headless` | `false` | Run Gazebo without GUI |
| `gz_verbosity` | `3` | Gazebo log verbosity (0–4) |
| `log_level` | `warn` | ROS 2 node log level |

Example — run headless:

```bash
ros2 launch testbot 4w_rsp.launch.py run_headless:=true use_rviz:=false
```

---

### 2. SLAM Mapping

Launches Gazebo + SLAM Toolbox in online async mode. Drive the robot around to build a map.

```bash
ros2 launch testbot slamap.launch.py
```

Optional arguments:

| Argument | Default | Description |
|---|---|---|
| `use_sim_time` | `true` | Use simulation clock |
| `rviz` | `true` | Launch RViz |
| `rviz_config` | `async_map.rviz` | RViz config file name |

Teleoperate the robot to map the environment:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/cmd_vel
```

When done mapping, save the map (see [Saving a Map](#6-saving-a-map)).

---

### 3. SLAM Localization (on saved map)

Localizes the robot on a previously saved map using SLAM Toolbox in localization mode.

```bash
ros2 launch testbot slamloc.launch.py
```

Optional arguments:

| Argument | Default | Description |
|---|---|---|
| `use_sim_time` | `true` | Use simulation clock |
| `rviz` | `true` | Launch RViz |
| `rviz_config` | `async_map.rviz` | RViz config file name |

> Make sure the serialized map files (`serialized.data` / `serialized.posegraph`) are referenced in `config/slam_loc.yaml`.

---

### 4. AMCL Localization (standalone)

Launches map server + AMCL + lifecycle manager for localization only, without the full Nav2 stack.

```bash
ros2 launch testbot amcloc.launch.py
```

Optional arguments:

| Argument | Default | Description |
|---|---|---|
| `map` | `maps/testhus_map.yaml` | Full path to map YAML file |

Use a different map:

```bash
ros2 launch testbot amcloc.launch.py map:=/path/to/your_map.yaml
```

---

### 5. Full Navigation (Nav2 + AMCL)

Launches the complete navigation stack: Gazebo, robot, AMCL localization, Nav2 (planner + controller + costmaps), and RViz with the Nav2 panel.

```bash
ros2 launch testbot nav.launch.py
```

Optional arguments:

| Argument | Default | Description |
|---|---|---|
| `yaml_filename` | `maps/testv1.yaml` | Map file for localization |
| `nav_params_file` | `config/nav.yaml` | Nav2 parameters file |
| `loc_params_file` | `config/amcloc.yaml` | AMCL parameters file |
| `use_sim_time` | `true` | Use simulation clock |

Use a different map:

```bash
ros2 launch testbot nav.launch.py yaml_filename:=/full/path/to/map.yaml
```

Once launched:
1. RViz opens with the Nav2 panel on the left
2. Use **2D Pose Estimate** in RViz to set the robot's initial position on the map
3. Use **Nav2 Goal** in RViz (or the Nav2 panel) to send a navigation goal
4. The robot will plan and follow a path autonomously

---

### 6. Saving a Map

After mapping with SLAM, save the map using `nav2_map_server`:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/botdev/src/testbot/maps/my_map
```

This creates `my_map.pgm` and `my_map.yaml` in the maps directory. Then rebuild so the new map is installed:

```bash
cd ~/botdev && colcon build --packages-select testbot --symlink-install
```

---

## Configuration Files

### `config/nav.yaml`
Full Nav2 parameter file covering:
- **AMCL** — particle filter localization (differential motion model)
- **bt_navigator** — behavior tree navigator
- **controller_server** — MPPI controller for local path following
- **local_costmap** — rolling window costmap using VoxelLayer + InflationLayer
- **global_costmap** — static + obstacle + inflation layers
- **planner_server** — SmacPlannerHybrid (Dubins motion model)
- **behavior_server** — spin, backup, drive_on_heading, wait behaviors
- **velocity_smoother** — smooths cmd_vel output
- **collision_monitor** — footprint-based approach collision checking

### `config/amcloc.yaml`
Standalone AMCL parameters used by `amcloc.launch.py` and `nav.launch.py` for localization.

### `config/ekf.yaml`
`robot_localization` EKF node configuration for fusing wheel odometry and IMU data into a stable `/odom` estimate.

### `config/slam_map.yaml` / `config/slam_loc.yaml`
SLAM Toolbox parameters for online async mapping and localization modes respectively.

---

## Key Components

### Robot Model
- Defined in `description/4w_testbot.xacro`
- 4-wheel differential drive with `base_footprint`, `base_link`, `lidar_link`, `imu_link`, `camera_link`
- Gazebo plugins: diff drive controller, LIDAR (LaserScan), IMU, camera

### Sensor Bridges (`4w_rsp.launch.py`)
The `ros_gz_bridge` node bridges the following topics from Ignition to ROS 2:

| Ignition Topic | ROS 2 Topic | Message Type |
|---|---|---|
| `/scan` | `/scan` | `sensor_msgs/LaserScan` |
| `/imu` | `/imu` | `sensor_msgs/Imu` |
| `/clock` | `/clock` | `rosgraph_msgs/Clock` |
| `/scan/points` | `/scan/points` | `sensor_msgs/PointCloud2` |

### Control Pipeline
```
Nav2 cmd_vel → twist_mux → /cmd_vel → relay → diff_drive_base_controller → wheels
```

### TF Tree
```
map → odom → base_footprint → base_link → lidar_link
                                         → imu_link
                                         → camera_link → camera_frame
                                         → fl_wheel / fr_wheel / rl_wheel / rr_wheel
```

---

## Challenges and Troubleshooting

### Maps not showing in RViz
- Confirm `localization_launch.py` is receiving the `map` argument — check terminal output for `map_server` startup logs
- In RViz, verify the `Map` display under the Displays panel is enabled and subscribed to `/map` with `Durability: Transient Local`
- Check that AMCL is active: `ros2 lifecycle get /amcl`

### AMCL not localizing / particle cloud scattered
- Set a **2D Pose Estimate** in RViz to give AMCL an initial position hint
- Ensure `/scan` topic is publishing: `ros2 topic hz /scan`
- Verify `base_frame_id` in `amcloc.yaml` matches your URDF (`base_footprint`)

### Navigation goals not being accepted
- Check all Nav2 nodes are in `active` lifecycle state: `ros2 lifecycle get /bt_navigator`
- Confirm the global and local costmaps are receiving scan data: `ros2 topic hz /global_costmap/costmap`

### LIDAR rays misaligned in Gazebo
![Screenshot from 2025-02-28 14-29-13](https://github.com/user-attachments/assets/b3c83e36-0250-4c98-bad1-50bb0546a82d)
- Caused by fixed joint lumping when converting URDF to SDF. Ensure the following is in your xacro for the lidar joint:
```xml
<gazebo reference="laser_joint">
  <preserveFixedJoint>true</preserveFixedJoint>
</gazebo>
```

### `ros2 control load_controller` fails
- Controllers must be loaded after `spawn_entity` completes. The launch file handles this via `RegisterEventHandler` / `OnProcessExit` chains — check that `spawn_entity` succeeded first
- Verify controller names match those in `4w_diff_drive_controller_velocity.yaml`

### TF world rotation / distorted SLAM map
![WhatsApp Image 2025-01-31 at 4 05 24 PM](https://github.com/user-attachments/assets/09e742e6-99db-4a75-93c8-2361319d9a77)
- Caused by `odom` frame drift from IMU noise during fast rotation
- Reduce rotational speed during teleoperation while mapping
- Verify EKF is running and fusing IMU + odom: `ros2 topic echo /odometry/filtered`

> Map generated after resolving TF frame alignment issue

![Resolved SLAM map](https://github.com/user-attachments/assets/4e8abd2e-03ae-41ec-b404-2a82de2e6a18)

### NVIDIA GPU / Docker issues
- If you see `nvml error: driver not loaded`, reinstall NVIDIA drivers and reconfigure the NVIDIA Container Toolkit
- Verify with: `nvidia-smi`

---

## Next Steps

- [ ] Improve localization stability with better EKF tuning
- [ ] Optimize MPPI controller parameters for smoother trajectories
- [ ] Add 3D obstacle avoidance using PointCloud2 from LIDAR
- [ ] Validate navigation stack on physical hardware

---

> Robot shown in Husarion world and TurtleBot Arena with TF tree visualization

![Testbot in simulation](https://github.com/user-attachments/assets/fa275afd-6fe1-4251-8eb2-502beef356f6)
![Testbot TF tree](https://github.com/user-attachments/assets/26ac0b15-961a-4dd8-9d2d-2f8a9f808fb3)
![Testbot world view](https://github.com/user-attachments/assets/4479aa42-eeda-4079-b791-50568485f316)



