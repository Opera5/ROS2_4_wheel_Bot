cmake_minimum_required(VERSION 3.5)
project(testbot)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ros_gz_bridge REQUIRED)
find_package(ros_ign_bridge REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)



if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # uncomment the line when a copyright and license is not present in all source files
  #set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # uncomment the line when this package is not in a git repo
  #set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

if(POLICY CMP0009)
  cmake_policy(SET CMP0009 NEW)
endif()

# Install Python src
install(PROGRAMS
  src/extract_velodyne_pointcloud.py
  src/extract_velodyne_with_tf.py
  src/extract_tf_poses.py
  src/extract_zed_pointcloud.py
  src/extract_2d_laser.py
  src/extract_zed_data.py
  src/zed_rgb_extract.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY src launch rviz config worlds models include description maps
  DESTINATION share/${PROJECT_NAME}
)

ament_package()


# <---------------------MISSION IN THE LAB ------------------------------>
#1. Xacro to URDF covert and compare
#2. scaling buggy version for simulation
#3. Workbench test on PC with Physical device