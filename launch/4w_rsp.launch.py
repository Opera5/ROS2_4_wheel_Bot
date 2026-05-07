
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription

import xacro

import launch
from launch.actions import (
    ExecuteProcess,
    DeclareLaunchArgument,
    RegisterEventHandler,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    NotSubstitution,
    AndSubstitution,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import launch_ros
import os



def generate_launch_description():



    # Process the URDF file
    pkg_path = os.path.join(get_package_share_directory('testbot'))
    default_rviz_config_path = os.path.join(pkg_path, "rviz/tbot.rviz")
    xacro_file = os.path.join(pkg_path,'description','4w_testbot.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    world_path = os.path.join(pkg_path, "worlds/husarion_world.sdf")
    ekf_path = os.path.join(pkg_path, "config/ekf.yaml")
    gz_models_path = os.path.join(pkg_path, "models")

    use_sim_time = LaunchConfiguration("use_sim_time")   # Check if we're told to use sim time
    use_localization = LaunchConfiguration("use_localization")
    use_rviz = LaunchConfiguration("use_rviz")
    log_level = LaunchConfiguration("log_level")
    gz_verbosity = LaunchConfiguration("gz_verbosity")
    run_headless = LaunchConfiguration("run_headless")

    
    # Create a robot_state_publisher node
    params = {'robot_description': robot_description_config.toxml(), 'use_sim_time': use_sim_time}

    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )
    
    rviz_node = Node(
        condition=IfCondition(AndSubstitution(NotSubstitution(run_headless), use_rviz)),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rvizconfig")],
    )

    ekfloc_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[ekf_path, {'use_sim_time': use_sim_time}],
    )

    #Twist mux node
    twistmux = Node(
    package='twist_mux',
    executable='twist_mux',
    name='twist_mux',
    output='screen',
    parameters=[os.path.join(get_package_share_directory('testbot'), 'config', 'twistmux.yaml')],
    remappings=[
        ('cmd_vel_out', '/cmd_vel')  # Output to actual robot/cmd_vel topic
    ]
    )


    # gazebo have to be executed with shell=False, or test_launch won't terminate it
    #   see: https://github.com/ros2/launch/issues/545
    # This code is form taken ros_gz_sim and modified to work with shell=False
    #   see: https://github.com/gazebosim/ros_gz/blob/ros2/ros_gz_sim/launch/gz_sim.launch.py.in
    gz_env = {'GZ_SIM_SYSTEM_PLUGIN_PATH':
           ':'.join([os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', default=''),
                     os.environ.get('LD_LIBRARY_PATH', default='')]),
           'IGN_GAZEBO_SYSTEM_PLUGIN_PATH':  # TODO(CH3): To support pre-garden. Deprecated.
                      ':'.join([os.environ.get('IGN_GAZEBO_SYSTEM_PLUGIN_PATH', default=''),
                                os.environ.get('LD_LIBRARY_PATH', default='')])}
    
    gazebo = [
        ExecuteProcess(
            condition=launch.conditions.IfCondition(run_headless),
            cmd=['ruby', FindExecutable(name="ign"), 'gazebo',  '-r', '-v', gz_verbosity, '-s', '--headless-rendering', world_path],
            output='screen',
            additional_env=gz_env, # type: ignore
            shell=False,
        ),
        ExecuteProcess(
            condition=launch.conditions.UnlessCondition(run_headless),
            cmd=['ruby', FindExecutable(name="ign"), 'gazebo',  '-r', '-v', gz_verbosity, world_path],
            output='screen',
            additional_env=gz_env, # type: ignore
            shell=False,
        ) 
    ]

    spawn_entity = Node(
        package="ros_ign_gazebo",
        executable="create",
        output="screen",
        arguments=[
            "-name",
            "test_bot",
            "-topic",
            "robot_description",
            "-z",
            "0.1",
            "-x",
            "0.0",
            "-y",
            "-2.0",
            "--ros-args",
            "--log-level",
            log_level,
        ],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Define the joint_state_publisher node
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time  # Set to true if using Gazebo or simulation time
        }]
    )


    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
           #"/scan@sensor_msgs/msg/LaserScan@ignition.msgs.LaserScan",
            "/scan@sensor_msgs/msg/LaserScan@ignition.msgs.LaserScan",
            "/imu@sensor_msgs/msg/Imu@ignition.msgs.IMU",
            "/sky_cam@sensor_msgs/msg/Image@ignition.msgs.Image",
            "/robot_cam@sensor_msgs/msg/Image@ignition.msgs.Image",
            "/camera_info@sensor_msgs/msg/CameraInfo@ignition.msgs.CameraInfo",
            # Clock message is necessary for the diff_drive_controller to accept commands https://github.com/ros-controls/gz_ros2_control/issues/106
            "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock",
            "/scan/points@sensor_msgs/msg/PointCloud2@ignition.msgs.PointCloudPacked",
        ],
        output="screen",
    )
    
    load_joint_state_controller = ExecuteProcess(
        name="activate_joint_state_broadcaster",
        cmd=[
            "ros2",
            "control",
            "load_controller",
            "--set-state",
            "active",
            "joint_state_broadcaster",
        ],
        shell=False,
        output="screen",
    )

    load_joint_trajectory_controller = ExecuteProcess(
        name="activate_diff_drive_base_controller",
        cmd=[
            "ros2",
            "control",
            "load_controller",
            "--set-state",
            "active",
            "diff_drive_base_controller",
        ],
        shell=False,
        output="screen",
    )

    load_diff_drive_controller = ExecuteProcess(
        name="activate_diff_drive_base_controller",
        cmd=["ros2", "control", "load_controller", "--set-state", "active", "diff_drive_base_controller"],
        shell=False,
        output="screen",
    )

    load_imu_broadcaster = ExecuteProcess(
        name="activate_imu_broadcaster",
        cmd=["ros2", "control", "load_controller", "--set-state", "active", "imu_broadcaster"],
        shell=False,
        output="screen",
    )

    relay_odom = Node(
        name="relay_odom",
        package="topic_tools",
        executable="relay",
        parameters=[
            {
                "input_topic": "/diff_drive_base_controller/odom",
                "output_topic": "/odom",
            }
        ],
        output="screen",
    )

    relay_cmd_vel = Node(
        name="relay_cmd_vel",
        package="topic_tools",
        executable="relay",
        parameters=[
            {
                "input_topic": "/cmd_vel",
                "output_topic": "/diff_drive_base_controller/cmd_vel_unstamped",
            }
        ],
        output="screen",
    )
    
    controller_config = os.path.join(pkg_path, 'config', '4w_diff_drive_controller_velocity.yaml')
    ros2_control_node = Node(
    package='controller_manager',
    executable='ros2_control_node',
    parameters=[controller_config],
    output='screen'
    )

    # Launch!
    return LaunchDescription([
            SetEnvironmentVariable(
                name="IGN_GAZEBO_RESOURCE_PATH",
                value=gz_models_path,
            ),
            SetEnvironmentVariable(
                name="IGN_GAZEBO_MODEL_PATH",
                value=gz_models_path,
            ),
            DeclareLaunchArgument(
                name="model",
                default_value=xacro_file,
                description="Absolute path to robot urdf file",
            ),
            DeclareLaunchArgument(
                name="use_rviz",
                default_value="True",
                description="Start RViz",
            ),
            DeclareLaunchArgument(
                name="rvizconfig",
                default_value=default_rviz_config_path,
                description="Absolute path to rviz config file",
            ),
            DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use sim time if true'),

            DeclareLaunchArgument(
                "gz_verbosity",
                default_value="3",
                description="Verbosity level for Ignition Gazebo (0~4).",
            ),
            DeclareLaunchArgument(
                "gz_args",
                default_value="",
                description="Extra args for Gazebo (ie. '-s' for running headless)",
            ),
            DeclareLaunchArgument(
                name="log_level",
                default_value="warn",
                description="The level of logging that is applied to all ROS 2 nodes launched by this script.",
            ),
            DeclareLaunchArgument(
                "run_headless",
                default_value="false",
                description="Whether to run Ignition Gazebo headless.",
            ),
            *gazebo,
            spawn_entity,
            bridge,
            #rviz_node,
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=spawn_entity,
                    on_exit=[load_joint_state_controller],
                )
            ),
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=load_joint_state_controller,
                    on_exit=[load_diff_drive_controller],
                )
            ),
            
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=load_diff_drive_controller,
                      on_exit=[load_imu_broadcaster])),
            robot_state_pub,
            relay_odom,
            ekfloc_node,
            relay_cmd_vel,
            ros2_control_node,
            #twistmux,
            joint_state_publisher_node,
        ]
    )

