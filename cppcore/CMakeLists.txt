cmake_minimum_required(VERSION 3.9)
project(kite_cppcore CXX C)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")

option(QK_WERROR "Make all warnings into errors" OFF)
option(QK_NATIVE_HDF5 "Use installed machine version of HDF5, if found" ON)
option(QK_NATIVE_EIGEN "Use installed machine version of Eigen, if found" ON)
option(QK_TESTS "Enable testing" ON)


include(download)
include(ExternalProject)

set(DOWNLOAD_HDF5 True)
if(QK_NATIVE_HDF5)
    find_package(HDF5 COMPONENTS CXX C HL)
    if(${HDF5_FOUND})
        set(HDF5_USE_STATIC_LIBRARIES ON)
        set(DOWNLOAD_HDF5 False)
        MESSAGE(STATUS "Using native machinge HDF5")
        MESSAGE(STATUS "Hdf5 Library:  ${HDF5_CXX_HL_LIBRARIES}")
        MESSAGE(STATUS "Hdf5Hl Library:  ${HDF5_CXX_LIBRARIES}")
    else()
        MESSAGE(STATUS "Couldn't find HDF5, installing it instead.")
    endif()
endif()

if(${DOWNLOAD_HDF5}) # failed to find HDF5, so install it
    set(ExternalProjectCMakeArgs
            "-DCMAKE_INSTALL_PREFIX=${hdf5_INSTALL_DIR}"
            "-DBUILD_SHARED_LIBS=ON"
            "-DHDF5_BUILD_CPP_LIB=ON"
            "-DHDF5_BUILD_EXAMPLES=OFF"       # Skip building examples
            "-DHDF5_BUILD_TOOLS=OFF"          # Skip building tools
            "-DHDF5_BUILD_HL_LIB=ON"          # Skip building high-level API libraries
            "-DHDF5_BUILD_FORTRAN=OFF"        # Skip building Fortran API
            "-DHDF5_BUILD_JAVA=OFF"           # Skip building Java wrappers
            "-DHDF5_BUILD_TESTING=OFF"        # Skip building tests
            )
    set(_hdf5_version "1.8.21")
    file(MAKE_DIRECTORY ${PROJECT_BINARY_DIR}/hdf5_local/src)
    ExternalProject_Add(hdf5_local
            DOWNLOAD_COMMAND curl https://support.hdfgroup.org/ftp/HDF5/current18/src/hdf5-${_hdf5_version}.tar.gz | tar xvz -C ${CMAKE_CURRENT_SOURCE_DIR}/deps/hdf5/src
            CMAKE_ARGS ${ExternalProjectCMakeArgs}
            SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/deps/hdf5/src/hdf5-${_hdf5_version}
            BINARY_DIR ${CMAKE_CURRENT_SOURCE_DIR}/deps/hdf5/build
            STAMP_DIR  ${CMAKE_CURRENT_SOURCE_DIR}/deps/hdf5/stamp
            TMP_DIR    ${CMAKE_CURRENT_SOURCE_DIR}/deps/hdf5/tmp
            INSTALL_COMMAND ""
            )
    set(HDF5_DIR ${CMAKE_CURRENT_SOURCE_DIR}/deps/hdf5)
    include_directories(
            ${HDF5_DIR}/src/hdf5-${_hdf5_version}/src
            ${HDF5_DIR}/src/hdf5-${_hdf5_version}/c++/src
            ${HDF5_DIR}/build
    )
    set(_hdf5_libs
            ${HDF5_DIR}/build/bin/libhdf5_cpp.a
            ${HDF5_DIR}/build/bin/libhdf5.a
            -ldl
            )
endif()

set(DOWNLOAD_EIGEN True)
if(QK_NATIVE_EIGEN)
    find_package(Eigen3)
    if(${EIGEN3_FOUND})
        set(DOWNLOAD_EIGEN False)
        MESSAGE(STATUS "Using native machinge Eigen3 library")
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
find_package(OpenMP)
MESSAGE(STATUS "OPENMP:  ${OPENMP_FOUND}")


add_subdirectory(kitex)
add_subdirectory(kitetools)
#if(QK_TESTS)
#    set(catch_url https://raw.githubusercontent.com/catchorg/Catch2/v\${VERSION}/single_include/catch2)
#    download_dependency(catch 2.13.10 ${catch_url} catch.hpp)
#    add_subdirectory(tests)
#endif()
