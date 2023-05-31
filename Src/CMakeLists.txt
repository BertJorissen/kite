cmake_minimum_required(VERSION 3.9)
project(KITExcxx)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_COMPILER "gcc")
set(CMAKE_CXX_COMPILER "g++")

add_library(kitecpp
        Generic.hpp
        Hamiltonian/aux.hpp
        Hamiltonian/Hamiltonian.hpp
        Hamiltonian/HamiltonianDefects.hpp
        Hamiltonian/HamiltonianRegular.hpp
        Hamiltonian/HamiltonianVacancies.hpp
        Lattice/Coordinates.hpp
        Lattice/LatticeStructure.hpp
        Simulation/Global.hpp
        Simulation/Simulation.hpp
        Simulation/SimulationGlobal.hpp
        Tools/ComplexTraits.hpp
        Tools/instantiate.hpp
        Tools/messages.hpp
        Tools/myHDF5.hpp
        Tools/queue.hpp
        Tools/Random.hpp
        Vector/KPM_Vector.hpp
        Vector/KPM_Vector2D.hpp
        Vector/KPM_Vector3D.hpp
        Vector/KPM_VectorBasis.hpp

        Hamiltonian/aux.cpp
        Hamiltonian/Hamiltonian.cpp
        Hamiltonian/HamiltonianDefects.cpp
        Hamiltonian/HamiltonianRegular.cpp
        Hamiltonian/HamiltonianVacancies.cpp
        Lattice/Coordinates.cpp
        Lattice/LatticeStructure.cpp
        Simulation/Global.cpp
        Simulation/GlobalSimulation.cpp
        Simulation/Simulation.cpp
        Simulation/SimulationARPES.cpp
        Simulation/SimulationCondDC.cpp
        Simulation/SimulationCondOpt.cpp
        Simulation/SimulationCondOpt2.cpp
        Simulation/SimulationDOS.cpp
        Simulation/SimulationGaussianWavePacket.cpp
        Simulation/SimulationLMU.cpp
        Simulation/SimulationSingleShot.cpp
        Tools/ComplexTraits.cpp
        Tools/Gamma1D.cpp
        Tools/Gamma2D.cpp
        Tools/Gamma3D.cpp
        Tools/myHDF5.cpp
        Tools/queue.cpp
        Tools/Random.cpp
        Tools/recursive_kpm.cpp
        Vector/KPM_Vector.cpp
        Vector/KPM_Vector2D.cpp
        Vector/KPM_Vector3D.cpp
        Vector/KPM_VectorBasis.cpp
        )

target_include_directories(kitecpp PUBLIC .)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

if(CMAKE_BUILD_TYPE MATCHES "Debug")
    add_definitions(-DDEBUG=1)
endif()

add_executable(KITEx main.cpp)
target_include_directories(KITEx PUBLIC .)

find_package(HDF5 COMPONENTS CXX C HL)
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
    MESSAGE(STATUS "Couldn't find Eigen3. Looking in ~/include/eigen3")
    target_include_directories(kitecpp PUBLIC ~/include/eigen3)
    target_include_directories(KITEx PUBLIC ~/include/eigen3)
endif()

set (CORRECT_CODING_FLAGS "")
find_package(OpenMP)
MESSAGE(STATUS "OPENMP:  ${OPENMP_FOUND}")
if (OPENMP_FOUND)
    target_link_libraries(kitecpp PUBLIC OpenMP::OpenMP_CXX)
    target_link_libraries(KITEx PUBLIC OpenMP::OpenMP_CXX)
    set (CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set (CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -O3 ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set (CMAKE_EXE_LINKER_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS}")
else()
    set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS}")
    set(CMAKE_CXX_FLAGS_DEBUG "${CORRECT_CODING_FLAGS} -g")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()
set_target_properties(kitecpp PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

target_link_libraries(KITEx PRIVATE kitecpp)
set(CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR})

set(compile_wp 1)
if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS 8.0.0)
    MESSAGE( STATUS "Cannot compile gaussian wavepacket")
    set(compile_wp 0)
endif()
add_definitions(-DCOMPILE_WAVEPACKET=${compile_wp})

set(RELEASE_FLAGS ${KITE_TOOLS_COMPILATION_FLAGS} ${KITE_TOOLS_WARNING_FLAGS} -O3)