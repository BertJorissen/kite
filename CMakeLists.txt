cmake_minimum_required(VERSION 3.9)

project(kite CXX)

set(CMAKE_CXX_STANDARD 17)  # We need the C+17 standard for advanced features like the Bessel-j-function

MESSAGE(STATUS "QK-- compiler is ${CMAKE_CXX_COMPILER_ID}") # See chat compiler we're using, some give weird results
if ("${CMAKE_CXX_COMPILER_ID}" MATCHES ".*Clang.*") # If Clang, the RPATH is always a bit tricky
    MESSAGE(STATUS "QK-- CLANG USED, other RPATH")
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

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cppcore/cmake") # include the copy and download scripts
option(QK_NATIVE_HDF5 "Use installed machine version of HDF5, if found" ON) # option to use machine HDF5
option(QK_NATIVE_EIGEN "Use installed machine version of Eigen, if found" ON) # option to use machine EIGEN
option(QK_CCACHE "Use CCache" ON) # option to use CCache. Python builds give problems when compiling different versions.


MESSAGE(STATUS "QK-- QK_NATIVE_HDF5:  ${QK_NATIVE_HDF5}") # Output the chosen options
MESSAGE(STATUS "QK-- QK_NATIVE_EIGEN: ${QK_NATIVE_EIGEN}")
MESSAGE(STATUS "QK-- QK_CCACHE:       ${QK_CCACHE}")

set(CMAKE_PREFIX_PATH ${QK_CMAKE_PREFIX_PATH} ${CMAKE_PREFIX_PATH}) # Add folders to the search path, for OMP and BOOST
MESSAGE(STATUS "QK-- CMAKE PREFIX PATH ${CMAKE_PREFIX_PATH}") # Display the search path
MESSAGE(STATUS "QK-- OpenMP Root Dir ${OpenMP_ROOT_DIR}") # Display the (tmp) build folder
if(NOT CMAKE_BUILD_TYPE) # force the user to set a release type (like Debug or Release)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build" FORCE)
endif()

if(QK_CCACHE) # configure CCache
    find_program(ccache_found ccache)
    if(ccache_found)
        set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
        set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
    endif()
endif()

include(download)
include(ExternalProject)


set(DOWNLOAD_HDF5 True) # By default, download it
if(QK_NATIVE_HDF5)
    find_package(HDF5 COMPONENTS CXX)
    if(${HDF5_FOUND})
        set(HDF5_USE_STATIC_LIBRARIES ON)
        set(DOWNLOAD_HDF5 False) # We found HDF5 and we want to use local version, disable download
        MESSAGE(STATUS "Using native machine HDF5")
        MESSAGE(STATUS "Hdf5-CXX Library:  ${HDF5_CXX_LIBRARIES}")
    else()
        MESSAGE(STATUS "Couldn't find HDF5, installing it instead.")
    endif()
endif()


if(${DOWNLOAD_HDF5}) # failed to find HDF5 or chose to not use local version, so install it
    set(ExternalProjectCMakeArgs
            "-DCMAKE_INSTALL_PREFIX=${hdf5_INSTALL_DIR}"
            "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}"
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
        set(HDF5_DOWNLOAD_VERSION "1.12.2") # this agrees with h5py==3.8.0
    endif()
    set(HDF5_USE_STATIC_LIBRARIES OFF) # we want shared libs
    major_minor_version(${HDF5_DOWNLOAD_VERSION} _hdf5_mm_version) # find the versions of the chosen HDF5-version
    MESSAGE(STATUS "QK-- HDF5 VERSION-${HDF5_DOWNLOAD_VERSION}-${_hdf5_mm_version}")
    set(HDF5_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cppcore/deps/hdf5)
    if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY) # if not set, use the default python-lib location
        set(hdf5_libs_folder ${CMAKE_CURRENT_SOURCE_DIR}/kite/lib)
    else()
        set(hdf5_libs_folder ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
    endif()
    set(hdf5_lib_name "libhdf5") # name of the HDF5-lib
    set(hdf5_cpp_lib_name "libhdf5_cpp") # name of the HDF5_cpp-lib
    set(hdf5_build_bin "${HDF5_DIR}/build/bin")
    if(APPLE)
        set(HDF_SL_EXT "dylib") # extension for apple-shared-libs
    elseif(WIN32)
        set(HDF_SL_EXT "lib") # extension for microsoft-shared-libs
        if((${CMAKE_BUILD_TYPE} STREQUAL "Debug") AND MSVC)
            MESSAGE(STATUS "QK-- DEBUG MODE ON MSVC, ADDING,'_D' to lib-name.")
            set(hdf5_lib_name "hdf5_D") # MSVC adds '_D' to the name if in debug mode
            set(hdf5_cpp_lib_name "hdf5_cpp_D")
        else()
            MESSAGE(STATUS "QK-- RELEASE MODE ON MSVC.")
            set(hdf5_build_bin "${HDF5_DIR}/build/bin/Release")
            set(hdf5_lib_name "libhdf5") # MSVC drops the 'lib'
            set(hdf5_cpp_lib_name "libhdf5_cpp")
        endif()
    else()
        set(HDF_SL_EXT "so") # extension for linux-shared-libs
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
            COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DFILES_WITH_WILDCARD=${hdf5_build_bin}/${hdf5_lib_name}.*${HDF_SL_EXT}* -DFILES_MOVE_DESTINATION=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
            COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DFILES_WITH_WILDCARD=${hdf5_build_bin}/${hdf5_cpp_lib_name}.*${HDF_SL_EXT}* -DFILES_MOVE_DESTINATION=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
            COMMAND ${CMAKE_COMMAND} -DEXECUTE_MOVE=TRUE -DFILES_WITH_WILDCARD=${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/COPYING  -DFILES_MOVE_DESTINATION=${hdf5_libs_folder} -P ${CMAKE_SOURCE_DIR}/cppcore/cmake/copy.cmake
            )
    set(hdf5_includes # header files for the build
            ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/src
            ${HDF5_DIR}/src/hdf5-${HDF5_DOWNLOAD_VERSION}/c++/src
            ${HDF5_DIR}/build/src
            ${HDF5_DIR}/build
            )
    include_directories(${hdf5_includes})

    set_target_properties(hdf5_local PROPERTIES POSITION_INDEPENDENT_CODE ON)

    # the new location of the libs, preferably in the kite/lib folder (set above)
    set(hdf5_libs ${hdf5_libs_folder}/${hdf5_lib_name}.${HDF_SL_EXT} ${hdf5_libs_folder}/${hdf5_cpp_lib_name}.${HDF_SL_EXT} )
endif()

find_package(OpenMP)
MESSAGE(STATUS "QK-- OPENMP:  ${OPENMP_FOUND}")

add_subdirectory(cppcore)
add_subdirectory(cppmodule)

if(EXISTS ${CMAKE_SOURCE_DIR}/docs)
    add_subdirectory(docs EXCLUDE_FROM_ALL)
endif()