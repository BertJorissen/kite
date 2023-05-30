cmake_minimum_required(VERSION 3.9)

project(kite CXX)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

if(CMAKE_BUILD_TYPE MATCHES "Debug")
  add_definitions(-DDEBUG=1)
endif()

add_subdirectory(Src)
# add_subdirectory(tools)
add_subdirectory(wrapper)
