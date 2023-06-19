cmake_minimum_required(VERSION 3.9)
project(kite_cppcore_kitetools CXX C)

add_library(cppcore_kitetools STATIC
        include/conddc/conductivity_dc.hpp
        include/optcond_1order/conductivity_optical.hpp
        include/optcond_2order/conductivity_2order.hpp
        include/optcond_2order/Gamma0.hpp
        include/optcond_2order/Gamma0photo.hpp
        include/optcond_2order/Gamma1.hpp
        include/optcond_2order/Gamma1photo.hpp
        include/optcond_2order/Gamma2.hpp
        include/optcond_2order/Gamma2photo.hpp
        include/optcond_2order/Gamma3.hpp
        include/optcond_2order/Gamma3photo.hpp
        include/spectral/arpes.hpp
        include/spectral/dos.hpp
        include/spectral/ldos.hpp
        include/tools/calculate.hpp
        include/tools/ComplexTraits.hpp
        include/tools/functions.hpp
        include/tools/messages.hpp
        include/tools/myHDF5.hpp
        include/tools/parse_input.hpp
        include/tools/systemInfo.hpp
        include/macros.hpp
        src/conddc/conductivity_dc.cpp
        src/conddc/fill.cpp
        src/optcond_1order/conductivity_optical.cpp
        src/optcond_2order/conductivity_2order.cpp
        src/optcond_2order/Gamma0.cpp
        src/optcond_2order/Gamma0photo.cpp
        src/optcond_2order/Gamma1.cpp
        src/optcond_2order/Gamma1photo.cpp
        src/optcond_2order/Gamma2.cpp
        src/optcond_2order/Gamma2photo.cpp
        src/optcond_2order/Gamma3.cpp
        src/optcond_2order/Gamma3photo.cpp
        src/spectral/arpes.cpp
        src/spectral/dos.cpp
        src/spectral/ldos.cpp
        src/tools/calculate.cpp
        src/tools/functions.cpp
        src/tools/myHDF5.cpp
        src/tools/parse_input.cpp
        src/tools/systemInfo.cpp
        )

add_library(kite::cppcore_kitetools ALIAS cppcore_kitetools)
target_include_directories(cppcore_kitetools PRIVATE include)

add_executable(KITE-tools src/main.cpp)
target_include_directories(KITE-tools PRIVATE include)


target_include_directories(cppcore_kitetools PRIVATE ${EIGEN3_INCLUDE_DIR})

if(${DOWNLOAD_HDF5}) # failed to find HDF5, so install it
	add_dependencies(KITE-tools hdf5_local)
	add_dependencies(cppcore_kitetools hdf5_local)
    target_link_libraries(KITE-tools PRIVATE ${_hdf5_libs})
    target_link_libraries(cppcore_kitetools PRIVATE ${_hdf5_libs})
else()
    target_include_directories(cppcore_kitetools SYSTEM PRIVATE ${HDF5_INCLUDE_DIR})
    target_include_directories(KITE-tools SYSTEM PRIVATE ${HDF5_INCLUDE_DIR})
    target_link_libraries(cppcore_kitetools PRIVATE ${HDF5_CXX_LIBRARIES})
    target_link_libraries(KITE-tools PRIVATE ${HDF5_CXX_LIBRARIES})
endif()

target_include_directories(cppcore_kitetools SYSTEM PUBLIC ${EIGEN3_INCLUDE_DIR})
target_include_directories(KITE-tools SYSTEM PUBLIC ${EIGEN3_INCLUDE_DIR})


if (OPENMP_FOUND)
    target_link_libraries(cppcore_kitetools PRIVATE OpenMP::OpenMP_CXX)
    target_link_libraries(KITE-tools PRIVATE OpenMP::OpenMP_CXX)
    set (CORRECT_CODING_FLAGS "-Wall ")
    set (CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} -g -O3 ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set (CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -g -O3 ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS}")
  else()
    set(CMAKE_CXX_FLAGS_DEBUG "-g")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()

set_target_properties(cppcore_kitetools PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

target_link_libraries(KITE-tools PRIVATE cppcore_kitetools)
set(CMAKE_MODULE_PATH ../..)

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

#link_directories(../../tools)
#include_directories(${Src})
#target_link_libraries(KITE-tools ${HDF5_CXX_LIBRARIES} )
#install (TARGETS KITE-tools DESTINATION bin)
