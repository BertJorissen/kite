cmake_minimum_required(VERSION 3.9)
project(KITEx CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_COMPILER "gcc")
set(CMAKE_CXX_COMPILER "g++")

list(APPEND CMAKE_MODULE_PATH "cmake")

add_library(kitecpp
        Generic.hpp
        include/hamiltonian/aux.hpp
        include/hamiltonian/Hamiltonian.hpp
        include/hamiltonian/HamiltonianDefects.hpp
        include/hamiltonian/HamiltonianRegular.hpp
        include/hamiltonian/HamiltonianVacancies.hpp
        include/lattice/Coordinates.hpp
        include/lattice/LatticeStructure.hpp
        include/simulation/Global.hpp
        include/simulation/Simulation.hpp
        include/simulation/SimulationGlobal.hpp
        include/tools/ComplexTraits.hpp
        include/tools/instantiate.hpp
        include/tools/messages.hpp
        include/tools/myHDF5.hpp
        include/tools/queue.hpp
        include/tools/Random.hpp
        include/vector/KPM_Vector.hpp
        include/vector/KPM_Vector2D.hpp
        include/vector/KPM_Vector3D.hpp
        include/vector/KPM_VectorBasis.hpp

        src/hamiltonian/aux.cpp
        src/hamiltonian/Hamiltonian.cpp
        src/hamiltonian/HamiltonianDefects.cpp
        src/hamiltonian/HamiltonianRegular.cpp
        src/hamiltonian/HamiltonianVacancies.cpp
        src/lattice/Coordinates.cpp
        src/lattice/LatticeStructure.cpp
        src/simulation/Global.cpp
        src/simulation/GlobalSimulation.cpp
        src/simulation/Simulation.cpp
        src/simulation/SimulationARPES.cpp
        src/simulation/SimulationCondDC.cpp
        src/simulation/SimulationCondOpt.cpp
        src/simulation/SimulationCondOpt2.cpp
        src/simulation/SimulationDOS.cpp
        src/simulation/SimulationGaussianWavePacket.cpp
        src/simulation/SimulationLMU.cpp
        src/simulation/SimulationSingleShot.cpp
        src/tools/ComplexTraits.cpp
        src/tools/Gamma1D.cpp
        src/tools/Gamma2D.cpp
        src/tools/Gamma3D.cpp
        src/tools/myHDF5.cpp
        src/tools/queue.cpp
        src/tools/Random.cpp
        src/tools/recursive_kpm.cpp
        src/vector/KPM_Vector.cpp
        src/vector/KPM_Vector2D.cpp
        src/vector/KPM_Vector3D.cpp
        src/vector/KPM_VectorBasis.cpp
        )

target_include_directories(kitecpp PUBLIC .)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

find_program(ccache_found ccache)
if(ccache_found)
    set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
    set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
endif()

if(CMAKE_BUILD_TYPE MATCHES "Debug")
    add_definitions(-DDEBUG=1)
endif()

add_executable(KITEx main.cpp)
target_include_directories(KITEx PUBLIC .)

find_package(HDF5 COMPONENTS CXX C HL)
include(download)

if(False)
    include(ExternalProject)
    set(ExternalProjectCMakeArgs
            "-DCMAKE_INSTALL_PREFIX=${hdf5_INSTALL_DIR}"
            "-DBUILD_SHARED_LIBS=ON"
            "-DHDF5_BUILD_CPP_LIB=ON"
            "-DHDF5_BUILD_EXAMPLES=OFF"       # Skip building examples
            "-DHDF5_BUILD_TOOLS=OFF"          # Skip building tools
            "-DHDF5_BUILD_HL_LIB=ON"         # Skip building high-level API libraries
            "-DHDF5_BUILD_FORTRAN=OFF"        # Skip building Fortran API
            "-DHDF5_BUILD_JAVA=OFF"           # Skip building Java wrappers
            "-DHDF5_BUILD_TESTING=OFF"        # Skip building tests
            )
    set(_hdf5_version "1.8.21")
    file(MAKE_DIRECTORY ${PROJECT_BINARY_DIR}/hdf5_local/src)
    ExternalProject_Add(hdf5_local
            DOWNLOAD_COMMAND curl https://support.hdfgroup.org/ftp/HDF5/current18/src/hdf5-${_hdf5_version}.tar.gz | tar xvz -C ${PROJECT_BINARY_DIR}/hdf5_local/src
            CMAKE_ARGS ${ExternalProjectCMakeArgs}
            SOURCE_DIR ${PROJECT_BINARY_DIR}/hdf5_local/src/hdf5-${_hdf5_version}
            BINARY_DIR ${PROJECT_BINARY_DIR}/hdf5_local/build
            STAMP_DIR  ${PROJECT_BINARY_DIR}/hdf5_local/stamp
            TMP_DIR    ${PROJECT_BINARY_DIR}/hdf5_local/tmp
            INSTALL_COMMAND ""
            )
    include_directories(
            ${PROJECT_BINARY_DIR}/hdf5_local/src/hdf5-${_hdf5_version}/src
            ${PROJECT_BINARY_DIR}/hdf5_local/src/hdf5-${_hdf5_version}/c++/src
            ${PROJECT_BINARY_DIR}/hdf5_local/build
    )
    set(_hdf5_libs
            ${PROJECT_BINARY_DIR}/hdf5_local/build/bin/libhdf5_cpp.a
            ${PROJECT_BINARY_DIR}/hdf5_local/build/bin/libhdf5.a
            -ldl
            )
    add_dependencies(KITEx hdf5_local)
    add_dependencies(kitecpp hdf5_local)
    target_link_libraries(KITEx PUBLIC ${_hdf5_libs})
    target_link_libraries(kitecpp PUBLIC ${_hdf5_libs})
endif()

if(${HDF5_FOUND})
    set(HDF5_USE_STATIC_LIBRARIES ON)
    target_include_directories(kitecpp PUBLIC ${HDF5_INCLUDE_DIR})
    target_link_libraries(kitecpp PUBLIC ${HDF5_CXX_LIBRARIES})
    target_include_directories(KITEx PUBLIC ${HDF5_INCLUDE_DIR})
    target_link_libraries(KITEx PUBLIC ${HDF5_CXX_LIBRARIES})

    MESSAGE(STATUS "Hdf5 Library:  ${HDF5_CXX_HL_LIBRARIES}")
    MESSAGE(STATUS "Hdf5Hl Library:  ${HDF5_CXX_LIBRARIES}")
else()
    MESSAGE(STATUS "Couldn't find HDF5")
endif()
MESSAGE(STATUS "Compiler:  ${CMAKE_CXX_COMPILER}")
include_directories(~/include/)

find_package(Eigen3)
if(${EIGEN3_FOUND})
    target_include_directories(kitecpp PUBLIC ${EIGEN3_INCLUDE_DIR})
    target_include_directories(KITEx PUBLIC ${EIGEN3_INCLUDE_DIR})
else()
    MESSAGE(STATUS "Couldn't find Eigen3. Downloading and installing Eigen3.")
    download_dependency(eigen3 3.4.0
            https://gitlab.com/libeigen/eigen/-/archive/\${VERSION}
            eigen-\${VERSION}.tar.gz */Eigen)
    if(${EIGEN3_FOUND})
        target_include_directories(kitecpp SYSTEM PUBLIC ${EIGEN3_INCLUDE_DIR})
        target_include_directories(KITEx SYSTEM PUBLIC ${EIGEN3_INCLUDE_DIR})
    else()
        MESSAGE(STATUS "Eigen3 still not found, using ~include/eigen3 instead.")
        target_include_directories(kitecpp PUBLIC ~/include/eigen3)
        target_include_directories(KITEx PUBLIC ~/include/eigen3)
    endif()
endif()

set(CORRECT_CODING_FLAGS "")
find_package(OpenMP)
MESSAGE(STATUS "OPENMP:  ${OPENMP_FOUND}")
if(OPENMP_FOUND)
    target_link_libraries(kitecpp PUBLIC OpenMP::OpenMP_CXX)
    target_link_libraries(KITEx PUBLIC OpenMP::OpenMP_CXX)
    set(CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -O3 ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set(CMAKE_EXE_LINKER_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS}")
else()
    set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS}")
    set(CMAKE_CXX_FLAGS_DEBUG "${CORRECT_CODING_FLAGS} -g")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()
set_target_properties(kitecpp PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

target_link_libraries(KITEx PRIVATE kitecpp)
set(CMAKE_MODULE_PATH ../..)

set(compile_wp 1)
if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS 8.0.0)
    MESSAGE( STATUS "Cannot compile gaussian wavepacket")
    set(compile_wp 0)
endif()
add_definitions(-DCOMPILE_WAVEPACKET=${compile_wp})

set(RELEASE_FLAGS ${KITE_TOOLS_COMPILATION_FLAGS} ${KITE_TOOLS_WARNING_FLAGS} -O3)