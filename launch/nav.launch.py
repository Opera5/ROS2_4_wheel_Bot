import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    # Map YAML
    map_file = LaunchConfiguration(
        'yaml_filename',
        default=os.path.join(
            get_package_share_directory('testbot'),
            'maps',
            'testv1.yaml'))

    # Navigation parameter YAML
    nav_params_file = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory('testbot'),
            'config',
            'nav.yaml'))
    
    # localization parameter YAML
    loc_params_file = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory('testbot'),
            'config',
            'amcloc.yaml'))

    # RViz config
    rviz_config_file = os.path.join(
        get_package_share_directory('testbot'),
        'rviz',
        'nav.rviz')

    # nav2_bringup launch dir
    nav2_bringup_launch_dir = os.path.join(
        get_package_share_directory('nav2_bringup'),
        'launch')

    return LaunchDescription([
        DeclareLaunchArgument(
            'yaml_filename',
            default_value=map_file,
            description='Full path to map yaml file'),

        DeclareLaunchArgument(
            'params_file',
            default_value=nav_params_file,
            description='Full path to the Nav2 parameters file'),
        
        DeclareLaunchArgument(
            'params_file',
            default_value=loc_params_file,
            description='Full path to the localization parameters file'),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock if true'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_launch_dir, 'navigation_launch.py')),
            launch_arguments={
                'map': map_file,  # MUST be passed as 'map' to nav2_bringup
                'use_sim_time': use_sim_time,
                'params_file': nav_params_file
            }.items()
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_launch_dir, 'localization_launch.py')),
            launch_arguments={
                'map': map_file,  # MUST be passed as 'map' to nav2_bringup
                'use_sim_time': use_sim_time,
                'params_file': loc_params_file
            }.items()
        ),

        # Launch Gazebo with your robot
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
            os.path.join(
            get_package_share_directory('testbot'), 'launch', '4w_rsp.launch.py')
                ),
            launch_arguments={'use_sim_time': 'true'}.items(),
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen')
    ])
