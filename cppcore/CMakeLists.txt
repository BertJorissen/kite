cmake_minimum_required(VERSION 3.9)

project(kite_cppcore CXX C)

set(CMAKE_CXX_STANDARD 17)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")

include(download)

set(DOWNLOAD_EIGEN True)
if(QK_NATIVE_EIGEN)
    find_package(Eigen3 QUIET)
    if(${EIGEN3_FOUND})
        set(DOWNLOAD_EIGEN False)
        MESSAGE(STATUS "Using native machine Eigen3 library")
    else()
        MESSAGE(STATUS "Couldn't find Eigen, installing it instead.")
    endif()
endif()

if(${DOWNLOAD_EIGEN}) # failed to find Eigen, so install it
    MESSAGE(STATUS "Downloading Eigen3")
    download_dependency(eigen3 3.4.0
            https://gitlab.com/libeigen/eigen/-/archive/\${VERSION}
            eigen-\${VERSION}.tar.gz */Eigen)
endif()
MESSAGE(STATUS "Eigen3 Library used: ${EIGEN3_INCLUDE_DIR}")

add_subdirectory(kitex)
add_subdirectory(kitetools)
