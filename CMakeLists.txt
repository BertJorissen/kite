cmake_minimum_required(VERSION 3.9)
project(kite CXX)

set(CMAKE_CXX_STANDARD 17)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cppcore/cmake")
option(QK_WERROR "Make all warnings into errors" OFF)
option(QK_NATIVE_HDF5 "Use installed machine version of HDF5, if found" OFF)
option(QK_NATIVE_EIGEN "Use installed machine version of Eigen, if found" ON)
option(QK_TESTS "Enable testing" ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build" FORCE)
endif()

find_program(ccache_found ccache)
if(ccache_found)
    set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
    set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
endif()

include(download)
include(ExternalProject)
set(CMAKE_BUILD_RPATH "$ORIGIN")
set(DOWNLOAD_HDF5 True)
if(QK_NATIVE_HDF5)
    find_package(HDF5 COMPONENTS CXX HL)
    if(${HDF5_FOUND})
        set(HDF5_USE_STATIC_LIBRARIES ON)
        set(DOWNLOAD_HDF5 False)
        MESSAGE(STATUS "Using native machine HDF5")
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
            "-DBUILD_STATIC_LIBS=ON"
            "-DHDF5_BUILD_CPP_LIB=ON"
            "-DHDF5_BUILD_C_LIB=ON"
            "-DHDF5_BUILD_HL_LIB=ON"
            "-DHDF5_BUILD_EXAMPLES=OFF"       # Skip building examples
            "-DHDF5_BUILD_TOOLS=OFF"          # Skip building tools
            "-DHDF5_BUILD_FORTRAN=OFF"        # Skip building Fortran API
            "-DHDF5_BUILD_JAVA=OFF"           # Skip building Java wrappers
            "-DHDF5_BUILD_TESTING=OFF"        # Skip building tests
            )
    set(_hdf5_version "1.12.2")
    set(HDF5_USE_STATIC_LIBRARIES ON)
    major_minor_version(${_hdf5_version} _hdf5_mm_version)
    file(MAKE_DIRECTORY ${PROJECT_BINARY_DIR}/hdf5_local/src)
    set(HDF5_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cppcore/deps/hdf5)
    if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
        set(hdf5_libs_folder ${CMAKE_CURRENT_SOURCE_DIR}/kite/lib/)
    else()
        set(hdf5_libs_folder ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
    endif()
    ExternalProject_Add(hdf5_local
            URL "https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-${_hdf5_mm_version}/hdf5-${_hdf5_version}/src/hdf5-${_hdf5_version}.tar.gz"
            CMAKE_ARGS ${ExternalProjectCMakeArgs}
            SOURCE_DIR ${HDF5_DIR}/src/hdf5-${_hdf5_version}
            BINARY_DIR ${HDF5_DIR}/build
            STAMP_DIR  ${HDF5_DIR}/stamp
            TMP_DIR    ${HDF5_DIR}/tmp
            INSTALL_COMMAND ""
            POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy ${HDF5_DIR}/build/bin/libhdf5.so ${hdf5_libs_folder}/libhdf5.so
            COMMAND ${CMAKE_COMMAND} -E copy ${HDF5_DIR}/build/bin/libhdf5.so.200 ${hdf5_libs_folder}/libhdf5.so.200
            COMMAND ${CMAKE_COMMAND} -E copy ${HDF5_DIR}/build/bin/libhdf5.so.200.2.0 ${hdf5_libs_folder}/libhdf5.so.200.2.0
            COMMAND ${CMAKE_COMMAND} -E copy ${HDF5_DIR}/build/bin/libhdf5_cpp.so ${hdf5_libs_folder}/libhdf5_cpp.so
            COMMAND ${CMAKE_COMMAND} -E copy ${HDF5_DIR}/build/bin/libhdf5_cpp.so.200 ${hdf5_libs_folder}/libhdf5_cpp.so.200
            COMMAND ${CMAKE_COMMAND} -E copy ${HDF5_DIR}/build/bin/libhdf5_cpp.so.200.2.0 ${hdf5_libs_folder}/libhdf5_cpp.so.200.2.0
            )
    set(hdf5_includes
            ${HDF5_DIR}/src/hdf5-${_hdf5_version}/src
            ${HDF5_DIR}/src/hdf5-${_hdf5_version}/c++/src
            ${HDF5_DIR}/build/src
            ${HDF5_DIR}/build
            )
    include_directories(${hdf5_includes})

    set_target_properties(hdf5_local PROPERTIES POSITION_INDEPENDENT_CODE ON)

    set(hdf5_libs ${hdf5_libs_folder}/libhdf5_cpp.so ${hdf5_libs_folder}/libhdf5.so.200)
endif()

add_subdirectory(cppcore)
add_subdirectory(cppmodule)

if(EXISTS ${CMAKE_SOURCE_DIR}/docs)
    add_subdirectory(docs EXCLUDE_FROM_ALL)
endif()

#if(TARGET catch)
#    add_custom_target(tests COMMAND $<TARGET_FILE:catch> COMMAND ${PYTHON_EXECUTABLE} -m pytest
#            DEPENDS _pybinding WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
#endif()
