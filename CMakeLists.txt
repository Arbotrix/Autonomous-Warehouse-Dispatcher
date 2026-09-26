cmake_minimum_required(VERSION 3.8)
project(warehouse_delivery_rbt)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

# Added 'config' to the install directory
install(DIRECTORY launch worlds urdf config maps
  DESTINATION share/${PROJECT_NAME}
)
install(PROGRAMS scripts/warehouse_navigator.py

  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
