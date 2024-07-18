cmake_minimum_required(VERSION 3.9)
project(kite_cppcore_kitex CXX C)
set(CMAKE_CXX_STANDARD 17)

add_library(cppcore_kitex STATIC
        include/Generic.hpp
        include/hamiltonian/HamiltonianAux.hpp
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
        src/hamiltonian/HamiltonianAux.cpp
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
        # src/tools/recursive_kpm.cpp
        src/vector/KPM_Vector.cpp
        src/vector/KPM_Vector2D.cpp
        src/vector/KPM_Vector3D.cpp
        src/vector/KPM_VectorBasis.cpp
        )

add_library(kite::cppcore_kitex ALIAS cppcore_kitex)
target_include_directories(cppcore_kitex SYSTEM PRIVATE include)
if (WIN32)
    target_link_libraries(cppcore_kitex PRIVATE Shlwapi)
endif ()

add_executable(KITEx src/main.cpp)
target_include_directories(KITEx SYSTEM PRIVATE include)


if(${DOWNLOAD_HDF5}) # failed to find HDF5, so install it
	add_dependencies(cppcore_kitex hdf5_local)
    target_include_directories(KITEx SYSTEM PRIVATE ${hdf5_includes})
    target_include_directories(cppcore_kitex SYSTEM PRIVATE ${hdf5_includes})
    target_link_libraries(KITEx PRIVATE ${hdf5_libs})
    target_link_libraries(cppcore_kitex PRIVATE ${hdf5_libs})
    MESSAGE(STATUS "Using downloaded HDF5")
else()
    target_include_directories(cppcore_kitex SYSTEM PRIVATE ${HDF5_INCLUDE_DIR})
    target_include_directories(KITEx SYSTEM PRIVATE ${HDF5_INCLUDE_DIR})
    target_link_libraries(cppcore_kitex PRIVATE ${HDF5_CXX_LIBRARIES})
    target_link_libraries(KITEx PRIVATE ${HDF5_CXX_LIBRARIES})
endif()

target_include_directories(cppcore_kitex SYSTEM PUBLIC ${EIGEN3_INCLUDE_DIR})

if(${OPENMP_FOUND})
    target_link_libraries(cppcore_kitex PRIVATE OpenMP::OpenMP_CXX)
    target_link_libraries(KITEx PRIVATE OpenMP::OpenMP_CXX)
    if (WIN32)
        set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    else ()
        set(CORRECT_CODING_FLAGS "-Wall ")
        set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -O3 ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    endif ()
    set(CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set(CMAKE_EXE_LINKER_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS}")
else()
    if (WIN32)
        set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_CXX_FLAGS}")
        set(CMAKE_CXX_FLAGS_DEBUG "${CORRECT_CODING_FLAGS}")
    else ()
        set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -O3 ${CMAKE_CXX_FLAGS}")
        set(CMAKE_CXX_FLAGS_DEBUG "${CORRECT_CODING_FLAGS} -g")
        set(CMAKE_CXX_FLAGS_RELEASE "-O3")
    endif ()
    set(CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_C_FLAGS}")
endif()


set(compile_wp 1)
set(use_bst 0)
if(${CMAKE_CXX_COMPILER_ID} MATCHES ".*Clang.*" OR
   (${CMAKE_CXX_COMPILER_ID} STREQUAL "GNU" AND ${CMAKE_CXX_COMPILER_VERSION} VERSION_LESS 8.0.0))
    MESSAGE(STATUS "Clang is used, or gcc<8.0.0. Try to fallback on Boost for C++17 feature 'std::cyl_bessel_j'")
    find_package(Boost CONFIG 1.20.0)
    if(Boost_FOUND)
        get_target_property(Boost_INCLUDE_DIRS Boost::headers INTERFACE_INCLUDE_DIRECTORIES)
        target_include_directories(cppcore_kitex SYSTEM PRIVATE ${Boost_INCLUDE_DIRS})
        MESSAGE(STATUS "BOOST was found: ${Boost_INCLUDE_DIRS}")
        set(use_bst 1)
    else()
        MESSAGE(STATUS "Didn't find BOOST, Guassian wavepacket won't be compiled")
        set(compile_wp 0)
    endif()
endif()

if(NOT MSVC)  # match default visibility of core library and extension module
    target_compile_options(cppcore_kitex PRIVATE -fvisibility=hidden)
endif ()
add_definitions(-DCOMPILE_WAVEPACKET=${compile_wp})
add_definitions(-DUSE_BOOST=${use_bst})

set_target_properties(cppcore_kitex PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

target_link_libraries(KITEx PRIVATE cppcore_kitex)
set_target_properties(KITEx PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR})
