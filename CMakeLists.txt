cmake_minimum_required(VERSION 3.9)
project(kite CXX)

set(CMAKE_CXX_STANDARD 17)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cppcore/cmake")
option(QK_NATIVE_HDF5 "Use installed machine version of HDF5, if found" ON)
option(QK_NATIVE_EIGEN "Use installed machine version of Eigen, if found" ON)

MESSAGE(HDF5-${QK_NATIVE_HDF5})
MESSAGE(EIGEN3-${QK_NATIVE_EIGEN})

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
    find_package(HDF5 COMPONENTS CXX)
    if(${HDF5_FOUND})
        set(HDF5_USE_STATIC_LIBRARIES ON)
        set(DOWNLOAD_HDF5 False)
        MESSAGE(STATUS "Using native machine HDF5")
        MESSAGE(STATUS "Hdf5-CXX Library:  ${HDF5_CXX_LIBRARIES}")
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
    if(NOT HDF5_DOWNLOAD_VERSION)
        set(HDF5_DOWNLOAD_VERSION "1.12.2")
    endif()
    set(HDF5_USE_STATIC_LIBRARIES OFF)
    major_minor_version(${HDF5_DOWNLOAD_VERSION} _hdf5_mm_version)
    MESSAGE(HDF5 VERSION-${HDF5_DOWNLOAD_VERSION}-${_hdf5_mm_version})
    set(HDF5_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cppcore/deps/hdf5)
    if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
        set(hdf5_libs_folder ${CMAKE_CURRENT_SOURCE_DIR}/kite/lib)
    else()
        set(hdf5_libs_folder ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
    endif()
    ExternalProject_Add(hdf5_local
            URL "https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-${_hdf5_mm_version}/hdf5-${HDF5_DOWNLOAD_VERSION}/src/hdf5-${HDF5_DOWNLOAD_VERSION}.tar.gz"
            CMAKE_ARGS ${ExternalProjectCMakeArgs}
            SOURCE_DIR ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}
            BINARY_DIR ${HDF5_DIR}/build
            STAMP_DIR  ${HDF5_DIR}/stamp
            TMP_DIR    ${HDF5_DIR}/tmp
            INSTALL_COMMAND ""
            POST_BUILD
            COMMAND ${CMAKE_COMMAND} -DHDF5_MOVE_FILES=TRUE -DHDF5_DIR=${HDF5_DIR} -DCMAKE_LIBRARY_OUTPUT_DIRECTORY=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
            )
    set(hdf5_includes
            ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/src
            ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/c++/src
            ${HDF5_DIR}/build/src
            ${HDF5_DIR}/build
            )
    include_directories(${hdf5_includes})

    set_target_properties(hdf5_local PROPERTIES POSITION_INDEPENDENT_CODE ON)

    set(hdf5_libs ${hdf5_libs_folder}/libhdf5_cpp.so ${hdf5_libs_folder}/libhdf5.so)
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
