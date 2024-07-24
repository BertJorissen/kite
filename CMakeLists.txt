cmake_minimum_required(VERSION 3.15)
project(kite CXX)

set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_CXX_STANDARD 17)

MESSAGE(STATUS "compiler is ${CMAKE_CXX_COMPILER_ID}")
MESSAGE(STATUS "CMAKE_CXX_COMPILER_VERSION: ${CMAKE_CXX_COMPILER_VERSION}")
MESSAGE(STATUS "CMAKE_BUILD_TYPE: ${CMAKE_BUILD_TYPE}")

# set the RPATH for the executable
if ("${CMAKE_CXX_COMPILER_ID}" MATCHES ".*Clang.*")
    MESSAGE(STATUS "CLANG USED, other RPATH")
    set(CMAKE_MACOSX_RPATH TRUE) # next 8 lines, I really don't know why this works lol
    set(CMAKE_SKIP_BUILD_RPATH FALSE)
    set(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)
    set(CMAKE_INSTALL_NAME_DIR "")
    set(CMAKE_INSTALL_RPATH "")
    set(CMAKE_SKIP_INSTALL_RPATH FALSE)
    set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
    set(CMAKE_SKIP_BUILD_RPATH FALSE)
    set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
else()
    set(CMAKE_BUILD_RPATH "$ORIGIN") # For the RPATH, just look in the same folder as the executable
    set(CMAKE_INSTALL_RPATH "$ORIGIN")
endif()

# settings for the project
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cppcore/cmake") # include the copy and download scripts
option(QK_NATIVE_HDF5 "Use installed machine version of HDF5, if found." ON) # option to use machine HDF5
option(QK_NATIVE_EIGEN "Use installed machine version of Eigen, if found." ON) # option to use machine EIGEN
option(QK_FORCE_NATIVE "Force installed machine version of Eigen3 and HDF5." OFF) # option to force native libs
option(QK_CCACHE "Use CCache" ON) # option to use CCache. Python builds give problems when compiling different versions.

# print out the settings
MESSAGE(STATUS "QK_NATIVE_HDF5:   ${QK_NATIVE_HDF5}")
MESSAGE(STATUS "QK_NATIVE_EIGEN:  ${QK_NATIVE_EIGEN}")
MESSAGE(STATUS "QK_FORCE_NATIVE:  ${QK_FORCE_NATIVE}")
MESSAGE(STATUS "QK_CCACHE:        ${QK_CCACHE}")

# set the default values for the paths
set(CMAKE_PREFIX_PATH ${QK_CMAKE_PREFIX_PATH} ${CMAKE_PREFIX_PATH})
MESSAGE(STATUS "CMAKE PREFIX PATH ${CMAKE_PREFIX_PATH}")
set(CMAKE_OSX_DEPLOYMENT_TARGET ${QK_CMAKE_OSX_DEPLOYMENT_TARGET} ${CMAKE_OSX_DEPLOYMENT_TARGET})
MESSAGE(STATUS "CMAKE_OSX_DEPLOYMENT_TARGET: ${CMAKE_OSX_DEPLOYMENT_TARGET}")
MESSAGE(STATUS "OpenMP Root Dir ${OpenMP_ROOT_DIR}")
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build" FORCE)
endif()

# configure CCache
if(QK_CCACHE)
    find_program(ccache_found ccache)
    if(ccache_found)
        MESSAGE(STATUS "CCache found, using it.")
        set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
        set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
    endif()
endif()


find_package(OpenMP)

# download the dependencies if needed
if (QK_FORCE_NATIVE)
    set(DOWNLOAD_HDF5 False)
    set(DOWNLOAD_EIGEN False)
    find_package(HDF5 COMPONENTS CXX REQUIRED)
    find_package(Eigen3 REQUIRED)
else ()
    list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cppcore/cmake")
    include(download)
    include(ExternalProject)

    set(DOWNLOAD_HDF5 True)
    set(DOWNLOAD_EIGEN True)

    if(QK_NATIVE_HDF5)
        find_package(HDF5 COMPONENTS CXX QUIET)
        if(HDF5_FOUND)
            set(HDF5_USE_STATIC_LIBRARIES ON)
            set(DOWNLOAD_HDF5 False)
            MESSAGE(STATUS "Using native machine HDF5, version '${HDF5_VERSION}' with CXX '${HDF5_CXX_LIBRARIES}'")
            find_package(Python3 QUIET)
            if(${Python3_FOUND})
                execute_process(COMMAND ${Python3_EXECUTABLE} -c "import h5py; print(h5py.version.hdf5_version)" OUTPUT_VARIABLE HDF5_PYTHON_VERSION)
                MESSAGE(STATUS "HDF5 h5py Version: ${HDF5_PYTHON_VERSION}")
                if (HDF5_PYTHON_VERSION VERSION_EQUAL HDF5_VERSION)
                    MESSAGE(STATUS "HDF5 Python Version matches HDF5 C++ Version, code will run correctly.")
                else()
                    MESSAGE(WARNING "HDF5 Python Version does not match HDF5 C++ Version, do NOT use the python interface. Unexpected behavior may occur.")
                endif()
            endif()
        else()
            MESSAGE(STATUS "Couldn't find HDF5, installing it instead.")
        endif()
    endif()

    if(QK_NATIVE_EIGEN)
        find_package(Eigen3 QUIET)
        if(${EIGEN3_FOUND})
            set(DOWNLOAD_EIGEN False)
            MESSAGE(STATUS "Using native machine Eigen3.")
        else()
            MESSAGE(STATUS "Couldn't find Eigen, installing it instead.")
        endif()
    endif()

    if(${DOWNLOAD_HDF5}) # failed to find HDF5 or chose to not use local version, so install it
        if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
            set(KITECORE_LIBS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/kite/lib)
        else()
            set(KITECORE_LIBS_DIR ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
        endif()
        MESSAGE(STATUS "KITECORE_LIBS_DIR: ${KITECORE_LIBS_DIR}")
        if(APPLE)
            set(SHARED_LIB_EXT "dylib")
        elseif(WIN32)
            set(SHARED_LIB_EXT "dll")
        else()
            set(SHARED_LIB_EXT "so")
        endif()
        message(STATUS "SHARED_LIB_EXT: ${SHARED_LIB_EXT}")

        if(NOT HDF5_DOWNLOAD_VERSION)
            set(HDF5_DOWNLOAD_VERSION "1.14.2")
        endif()
        major_minor_version(${HDF5_DOWNLOAD_VERSION} _hdf5_mm_version)
        MESSAGE(STATUS "HDF5 VERSION-${HDF5_DOWNLOAD_VERSION}-${_hdf5_mm_version}")

        set(HDF5_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cppcore/deps/hdf5)

        set(HDF5_ExternalProjectCMakeArgs
                "-DCMAKE_INSTALL_PREFIX=${HDF5_DIR}/install"
                "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}"
                "-DBUILD_SHARED_LIBS=ON"
                "-DBUILD_STATIC_LIBS=OFF"
                "-DHDF5_BUILD_CPP_LIB=ON"
                "-DHDF5_BUILD_C_LIB=OFF"
                "-DHDF5_BUILD_HL_LIB=OFF"
                "-DHDF5_BUILD_EXAMPLES=OFF"       # Skip building examples
                "-DHDF5_BUILD_TOOLS=OFF"          # Skip building tools
                "-DHDF5_BUILD_FORTRAN=OFF"        # Skip building Fortran API
                "-DHDF5_BUILD_JAVA=OFF"           # Skip building Java wrappers
                "-DHDF5_BUILD_TESTING=OFF"        # Skip building tests
                "-DCMAKE_CXX_FLAGS=-DH5_BUILT_AS_DYNAMIC_LIB"
                "-DH5_BUILT_AS_DYNAMIC_LIB=ON"
                "-DH5_ENABLE_SHARED_LIB=YES"
                )

        if(WIN32)
            set(HDF5_PRE "")
            set(HDF5_EXT ${SHARED_LIB_EXT})
            set(HDF5_BUILD_DIR ${HDF5_DIR}/build/bin/Release)
        else()
            set(HDF5_PRE "lib")
            set(HDF5_EXT "*${SHARED_LIB_EXT}*")
            set(HDF5_BUILD_DIR ${HDF5_DIR}/build/bin)
        endif()
        ExternalProject_Add(hdf5_local
                URL "https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-${_hdf5_mm_version}/hdf5-${HDF5_DOWNLOAD_VERSION}/src/hdf5-${HDF5_DOWNLOAD_VERSION}.tar.gz"
                CMAKE_ARGS ${HDF5_ExternalProjectCMakeArgs}
                SOURCE_DIR ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}
                BINARY_DIR ${HDF5_DIR}/build
                STAMP_DIR  ${HDF5_DIR}/stamp
                TMP_DIR    ${HDF5_DIR}/tmp
                DOWNLOAD_EXTRACT_TIMESTAMP TRUE
                INSTALL_COMMAND ""
                POST_BUILD
                COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DFILES_WITH_WILDCARD=${HDF5_BUILD_DIR}/${HDF5_PRE}hdf5.${HDF5_EXT} -DFILES_MOVE_DESTINATION=${KITECORE_LIBS_DIR} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
                COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DFILES_WITH_WILDCARD=${HDF5_BUILD_DIR}/${HDF5_PRE}hdf5_cpp.${HDF5_EXT} -DFILES_MOVE_DESTINATION=${KITECORE_LIBS_DIR} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
                COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DFILES_WITH_WILDCARD=${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/COPYING  -DFILES_MOVE_DESTINATION=${KITECORE_LIBS_DIR} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
        )
        set(hdf5_includes
                ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/src
                ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/src/H5FDsubfiling
                ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/c++/src
                ${HDF5_DIR}/build/src
                ${HDF5_DIR}/build
                )
        set_target_properties(hdf5_local PROPERTIES POSITION_INDEPENDENT_CODE ON)
        if (WIN32)
            set(hdf5_libs ${HDF5_BUILD_DIR}/hdf5.lib ${HDF5_BUILD_DIR}/hdf5_cpp.lib)
        else()
            set(hdf5_libs ${KITECORE_LIBS_DIR}/${HDF5_PRE}hdf5.${SHARED_LIB_EXT} ${KITECORE_LIBS_DIR}/${HDF5_PRE}hdf5_cpp.${SHARED_LIB_EXT})
        endif()
        MESSAGE(STATUS "HDF5_INCLUDES: ${hdf5_includes}")
        MESSAGE(STATUS "HDF5_LIBS: ${hdf5_libs}")
    endif()

    if(DOWNLOAD_EIGEN) # failed to find Eigen, so install it
        MESSAGE(STATUS "Downloading Eigen3")
        download_dependency(eigen3 3.4.0
                https://gitlab.com/libeigen/eigen/-/archive/\${VERSION}
                eigen-\${VERSION}.tar.gz */Eigen)
    endif()
endif()
MESSAGE(STATUS "Eigen3 Library used: ${EIGEN3_INCLUDE_DIR}")

add_subdirectory(cppcore)
add_subdirectory(cppmodule)

if(EXISTS ${CMAKE_SOURCE_DIR}/docs)
    add_subdirectory(docs EXCLUDE_FROM_ALL)
endif()
