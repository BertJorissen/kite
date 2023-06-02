cmake_minimum_required(VERSION 3.9)
project(KITEtoolscxx)

set(CMAKE_C_COMPILER "gcc")
set(CMAKE_CXX_COMPILER "g++")
set(CMAKE_CXX_STANDARD 17)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")

add_library(kitetoolscpp
        Src/CondDC/conductivity_dc.hpp
        Src/OptCond_1order/conductivity_optical.hpp
        Src/OptCond_2order/conductivity_2order.hpp
        Src/OptCond_2order/Gamma0.hpp
        Src/OptCond_2order/Gamma0photo.hpp
        Src/OptCond_2order/Gamma1.hpp
        Src/OptCond_2order/Gamma1photo.hpp
        Src/OptCond_2order/Gamma2.hpp
        Src/OptCond_2order/Gamma2photo.hpp
        Src/OptCond_2order/Gamma3.hpp
        Src/OptCond_2order/Gamma3photo.hpp
        Src/Spectral/arpes.hpp
        Src/Spectral/dos.hpp
        Src/Spectral/ldos.hpp
        Src/Tools/calculate.hpp
        Src/Tools/ComplexTraits.hpp
        Src/Tools/functions.hpp
        Src/Tools/messages.hpp
        Src/Tools/myHDF5.hpp
        Src/Tools/parse_input.hpp
        Src/Tools/systemInfo.hpp
        Src/macros.hpp

        Src/CondDC/conductivity_dc.cpp
        Src/CondDC/fill.cpp
        Src/OptCond_1order/conductivity_optical.cpp
        Src/OptCond_2order/conductivity_2order.cpp
        Src/OptCond_2order/Gamma0.cpp
        Src/OptCond_2order/Gamma0photo.cpp
        Src/OptCond_2order/Gamma1.cpp
        Src/OptCond_2order/Gamma1photo.cpp
        Src/OptCond_2order/Gamma2.cpp
        Src/OptCond_2order/Gamma2photo.cpp
        Src/OptCond_2order/Gamma3.cpp
        Src/OptCond_2order/Gamma3photo.cpp
        Src/Spectral/arpes.cpp
        Src/Spectral/dos.cpp
        Src/Spectral/ldos.cpp
        Src/Tools/calculate.cpp
        Src/Tools/functions.cpp
        Src/Tools/myHDF5.cpp
        Src/Tools/parse_input.cpp
        Src/Tools/systemInfo.cpp
        )

target_include_directories(kitetoolscpp PUBLIC Src)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

if(CMAKE_BUILD_TYPE MATCHES "Debug")
  add_definitions(-DDEBUG=1)
endif()

add_executable(KITE-tools Src/main.cpp)
target_include_directories(KITE-tools PUBLIC .)

find_package(HDF5 COMPONENTS CXX C HL)

include(download)

include(ExternalProject)
set(ExternalProjectCMakeArgs
        -DHDF5_BUILD_CPP_LIB=ON
        )
set(_hdf5_version "1.8.21")
file(MAKE_DIRECTORY ${PROJECT_BINARY_DIR}/hdf5_localx/src)
ExternalProject_Add(hdf5_localx
        DOWNLOAD_COMMAND curl https://support.hdfgroup.org/ftp/HDF5/current18/src/hdf5-${_hdf5_version}.tar.gz | tar xvz -C ${PROJECT_BINARY_DIR}/hdf5_localx/src
        CMAKE_ARGS ${ExternalProjectCMakeArgs}
        SOURCE_DIR ${PROJECT_BINARY_DIR}/hdf5_localx/src/hdf5-${_hdf5_version}
        BINARY_DIR ${PROJECT_BINARY_DIR}/hdf5_localx/build
        STAMP_DIR  ${PROJECT_BINARY_DIR}/hdf5_localx/stamp
        TMP_DIR    ${PROJECT_BINARY_DIR}/hdf5_localx/tmp
        INSTALL_COMMAND ""
        )
include_directories(
        ${PROJECT_BINARY_DIR}/hdf5_localx/src/hdf5-${_hdf5_version}/src
        ${PROJECT_BINARY_DIR}/hdf5_localx/src/hdf5-${_hdf5_version}/c++/src
        ${PROJECT_BINARY_DIR}/hdf5_localx/build
)
set(_hdf5_libsx
        ${PROJECT_BINARY_DIR}/hdf5_localx/build/bin/libhdf5_cpp.a
        ${PROJECT_BINARY_DIR}/hdf5_localx/build/bin/libhdf5.a
        -ldl
        )
add_dependencies(KITE-tools hdf5_localx)
add_dependencies(kitetoolscpp hdf5_localx)
target_link_libraries(KITE-tools PUBLIC ${_hdf5_libsx})
target_link_libraries(kitetoolscpp PUBLIC ${_hdf5_libsx})

if(${HDF5_FOUND})
#    set(HDF5_USE_STATIC_LIBRARIES ON)
#    target_include_directories(kitetoolscpp PUBLIC ${HDF5_INCLUDE_DIR})
#    target_link_libraries(kitetoolscpp PUBLIC ${HDF5_CXX_LIBRARIES})
#    target_include_directories(KITE-tools PUBLIC ${HDF5_INCLUDE_DIR})
#    target_link_libraries(KITE-tools PUBLIC ${HDF5_CXX_LIBRARIES})

    MESSAGE(STATUS "Hdf5 Library:  ${HDF5_CXX_HL_LIBRARIES}")
    MESSAGE(STATUS "Hdf5Hl Library:  ${HDF5_CXX_LIBRARIES}")
else()
  MESSAGE(FATAL_ERROR  "Couldn't find hdf5")
endif()
MESSAGE(STATUS "Compiler:  ${CMAKE_CXX_COMPILER}")
include_directories(~/include/)


find_package(Eigen3)
if(${EIGEN3_FOUND})
    target_include_directories(kitetoolscpp PUBLIC ${EIGEN3_INCLUDE_DIR})
    target_include_directories(KITE-tools PUBLIC ${EIGEN3_INCLUDE_DIR})
else()
  MESSAGE(STATUS "Couldn't find Eigen3. Looking in ~/include")
  target_include_directories(kitetoolscpp PUBLIC ~/include/eigen3)
  target_include_directories(KITE-tools PUBLIC ~/include/eigen3)
endif()


find_package(OpenMP)
MESSAGE(STATUS "OPENMP:  ${OPENMP_FOUND}")      
if (OPENMP_FOUND)
    target_link_libraries(kitetoolscpp PUBLIC OpenMP::OpenMP_CXX)
    target_link_libraries(KITE-tools PUBLIC OpenMP::OpenMP_CXX)
    set (CORRECT_CODING_FLAGS "-Wall ")
    set (CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} -g -O3 ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set (CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -g -O3 ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS}")
  else()
    set(CMAKE_CXX_FLAGS_DEBUG "-g")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()
set_target_properties(kitetoolscpp PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

target_link_libraries(KITE-tools PRIVATE kitetoolscpp)
set(CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR})

set(SYSTEM_NAME ${CMAKE_HOST_SYSTEM_NAME})
cmake_host_system_information(RESULT _host_name QUERY HOSTNAME)
set(MACHINE_NAME ${_host_name})
#MESSAGE(STATUS "DIR" ${PROJECT_BINARY_DIR})
#include_directories(${PROJECT_BINARY_DIR}/Src)

#FILE(GLOB_RECURSE SRCFILES Src/*.cpp)
#FILE(GLOB SRCFILES Src/*.cpp)
#FILE(GLOB SRCFILES2 Src/Spectral/*.cpp)
#FILE(GLOB SRCFILES3 Src/Tools/*.cpp)
#FILE(GLOB SRCFILES4 Src/CondDC/*.cpp)
#FILE(GLOB SRCFILES5 Src/OptCond_1order/*.cpp)
#FILE(GLOB SRCFILES6 Src/OptCond_2order/*.cpp)
#add_executable(KITE-tools ${SRCFILES})# ${SRCFILES2} ${SRCFILES3} ${SRCFILES4} ${SRCFILES5} ${SRCFILES6})
string(TIMESTAMP TODAY "(yymmdd) %Y-%m-%d %H:%M:%S")
#configure_file (
#  "Src/compiletime_info.h.in"
#  "Src/compiletime_info.h"
#  )

link_directories(.)
#include_directories(${Src})
#target_link_libraries(KITE-tools ${HDF5_CXX_LIBRARIES} )
#install (TARGETS KITE-tools DESTINATION bin)
