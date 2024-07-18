cmake_minimum_required(VERSION 3.15)
project(kite CXX)

set(CMAKE_CXX_STANDARD 17)

MESSAGE(STATUS "compiler is ${CMAKE_CXX_COMPILER_ID}")
MESSAGE(STATUS "CMAKE_CXX_COMPILER_VERSION: ${CMAKE_CXX_COMPILER_VERSION}")
MESSAGE(STATUS "CMAKE_BUILD_TYPE: ${CMAKE_BUILD_TYPE}")
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
    set(CMAKE_BUILD_RPATH "$ORIGIN")
    set(CMAKE_INSTALL_RPATH "$ORIGIN")
endif()

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cppcore/cmake")
option(QK_NATIVE_HDF5 "Use installed machine version of HDF5, if found" ON)
option(QK_NATIVE_EIGEN "Use installed machine version of Eigen, if found" ON)
option(QK_CCACHE "Use CCache" ON)


MESSAGE(STATUS "QK_NATIVE_HDF5:  ${QK_NATIVE_HDF5}")
MESSAGE(STATUS "QK_NATIVE_EIGEN: ${QK_NATIVE_EIGEN}")
MESSAGE(STATUS "QK_CCACHE:       ${QK_CCACHE}")

set(CMAKE_PREFIX_PATH ${QK_CMAKE_PREFIX_PATH} ${CMAKE_PREFIX_PATH})
MESSAGE(STATUS "CMAKE PREFIX PATH ${CMAKE_PREFIX_PATH}")
MESSAGE(STATUS "OpenMP Root Dir ${OpenMP_ROOT_DIR}")
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build" FORCE)
endif()

if(QK_CCACHE)
    find_program(ccache_found ccache)
    if(ccache_found)
        MESSAGE(STATUS "CCache found, using it.")
        set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
        set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
    endif()
endif()

include(download)
include(ExternalProject)


find_package(OpenMP REQUIRED)
MESSAGE(STATUS "OPENMP:  ${OPENMP_FOUND}")


set(DOWNLOAD_HDF5 True)
if(QK_NATIVE_HDF5)
    find_package(HDF5 COMPONENTS CXX HL)
    if(${HDF5_FOUND})
        set(HDF5_USE_STATIC_LIBRARIES ON)
        set(DOWNLOAD_HDF5 False)
        MESSAGE(STATUS "Using native machine HDF5, version: ${HDF5_VERSION}")
        MESSAGE(STATUS "Hdf5-CXX Library:  ${HDF5_CXX_LIBRARIES}")

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


if(${DOWNLOAD_HDF5}) # failed to find HDF5, so install it
    set(ExternalProjectCMakeArgs
            "-DCMAKE_INSTALL_PREFIX=${hdf5_INSTALL_DIR}"
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

    if(NOT HDF5_DOWNLOAD_VERSION)
        set(HDF5_DOWNLOAD_VERSION "1.14.2")
    endif()
    set(HDF5_USE_STATIC_LIBRARIES OFF)
    major_minor_version(${HDF5_DOWNLOAD_VERSION} _hdf5_mm_version)
    MESSAGE(STATUS "HDF5 VERSION-${HDF5_DOWNLOAD_VERSION}-${_hdf5_mm_version}")
    set(HDF5_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cppcore/deps/hdf5)
    if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
        set(hdf5_libs_folder ${CMAKE_CURRENT_SOURCE_DIR}/kite/lib)
    else()
        set(hdf5_libs_folder ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
    endif()
    set(HDF5_BTP "")
    if(APPLE)
        set(HDF_SL_PRE "lib")
        set(HDF_SL_EXT "dylib")
        set(HDF_SL_EXT_WILD "*${HDF_SL_EXT}*")
        set(HDF_BUILD_DIR ${HDF5_DIR}/build/bin)
    elseif(WIN32)
        set(HDF_SL_PRE "")
        set(HDF_SL_EXT "dll")
        set(HDF_SL_EXT_WILD ${HDF_SL_EXT})
        string(TOUPPER "${CMAKE_BUILD_TYPE}" BUILD_TYPE_UPPER)
        if (BUILD_TYPE_UPPER STREQUAL "DEBUG")
            set(HDF_BUILD_DIR ${HDF5_DIR}/build/bin/Debug)
            set(HDF5_BTP "_D")
        elseif (BUILD_TYPE_UPPER STREQUAL "RELEASE")
            set(HDF_BUILD_DIR ${HDF5_DIR}/build/bin/Release)
        else ()
            MESSAGE(FATAL_ERROR "Unknown build type: ${CMAKE_BUILD_TYPE}")
        endif ()
    else()
        set(HDF_SL_PRE "lib")
        set(HDF_SL_EXT "so")
        set(HDF_SL_EXT_WILD "*${HDF_SL_EXT}*")
        set(HDF_BUILD_DIR ${HDF5_DIR}/build/bin)
    endif()
    ExternalProject_Add(hdf5_local
            URL "https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-${_hdf5_mm_version}/hdf5-${HDF5_DOWNLOAD_VERSION}/src/hdf5-${HDF5_DOWNLOAD_VERSION}.tar.gz"
            CMAKE_ARGS ${ExternalProjectCMakeArgs}
            SOURCE_DIR ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}
            BINARY_DIR ${HDF5_DIR}/build
            STAMP_DIR  ${HDF5_DIR}/stamp
            TMP_DIR    ${HDF5_DIR}/tmp
            DOWNLOAD_EXTRACT_TIMESTAMP TRUE
            INSTALL_COMMAND ""
            POST_BUILD
            COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DWIN=FALSE -DFILES_WITH_WILDCARD=${HDF_BUILD_DIR}/${HDF_SL_PRE}hdf5${HDF5_BTP}.${HDF_SL_EXT_WILD} -DFILES_MOVE_DESTINATION=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
            COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DWIN=FALSE -DFILES_WITH_WILDCARD=${HDF_BUILD_DIR}/${HDF_SL_PRE}hdf5_cpp${HDF5_BTP}.${HDF_SL_EXT_WILD} -DFILES_MOVE_DESTINATION=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
            COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DWIN=TRUE -DFILES_WITH_WILDCARD=${HDF_BUILD_DIR}/${HDF_SL_PRE}hdf5${HDF5_BTP}.lib -DFILES_MOVE_DESTINATION=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
            COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DWIN=TRUE -DFILES_WITH_WILDCARD=${HDF_BUILD_DIR}/${HDF_SL_PRE}hdf5_cpp${HDF5_BTP}.lib -DFILES_MOVE_DESTINATION=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
            COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DWIN=FALSE -DFILES_WITH_WILDCARD=${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/COPYING  -DFILES_MOVE_DESTINATION=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
    )
    set(hdf5_includes
            ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/src
            ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/src/H5FDsubfiling
            ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/c++/src
            ${HDF5_DIR}/build/src
            ${HDF5_DIR}/build
            )
    include_directories(${hdf5_includes})

    set_target_properties(hdf5_local PROPERTIES POSITION_INDEPENDENT_CODE ON)
    if (WIN32)
        set(hdf5_libs ${hdf5_libs_folder}/hdf5${HDF5_BTP}.lib ${hdf5_libs_folder}/hdf5_cpp${HDF5_BTP}.lib)
        set(hdf5_libs ${hdf5_libs} ${hdf5_libs_folder}/hdf5${HDF5_BTP}.${HDF_SL_EXT} ${hdf5_libs_folder}/hdf5_cpp${HDF5_BTP}.${HDF_SL_EXT})
    else()
        set(hdf5_libs ${hdf5_libs_folder}/${HDF_SL_PRE}hdf5.${HDF_SL_EXT} ${hdf5_libs_folder}/${HDF_SL_PRE}hdf5_cpp.${HDF_SL_EXT})
    endif()
    MESSAGE(STATUS "HDF5_INCLUDES: ${hdf5_includes}")
    MESSAGE(STATUS "HDF5_LIBS: ${hdf5_libs}")
endif()

add_subdirectory(cppcore)
add_subdirectory(cppmodule)

if(EXISTS ${CMAKE_SOURCE_DIR}/docs)
    add_subdirectory(docs EXCLUDE_FROM_ALL)
endif()
