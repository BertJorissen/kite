set(PYBIND11_PYTHON_VERSION 3.5 CACHE STRING "Minimum required Python version")
add_subdirectory(deps/pybind11 EXCLUDE_FROM_ALL)

set(CMAKE_CXX_STANDARD 17)

pybind11_add_module(_kite src/main.cpp)

if(${DOWNLOAD_HDF5})
    MESSAGE("qqssddffgg")
    MESSAGE("_kite " ${_hdf5_includes} ${_hdf5_libs})
    add_dependencies(_kite hdf5_local)
    target_include_directories(_kite SYSTEM PRIVATE ${_hdf5_includes})
    target_link_libraries(_kite PRIVATE ${_hdf5_libs})
endif()
target_include_directories(_kite SYSTEM PUBLIC ${EIGEN3_INCLUDE_DIR})

target_include_directories(_kite SYSTEM PRIVATE ../cppcore/kitex/include)
target_include_directories(_kite SYSTEM PRIVATE ../cppcore/kitetools/include)

target_link_libraries(_kite PRIVATE cppcore_kitex)
target_link_libraries(_kite PRIVATE cppcore_kitetools)

if(NOT MSVC)  # match default visibility of core library and extension module
    target_compile_options(cppcore_kitex PRIVATE -fvisibility=hidden)
    target_compile_options(cppcore_kitetools PRIVATE -fvisibility=hidden)
endif()
set(CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -O3 ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
set(CMAKE_EXE_LINKER_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS}")

set_target_properties(cppcore_kitex PROPERTIES POSITION_INDEPENDENT_CODE TRUE)
set_target_properties(cppcore_kitetools PROPERTIES POSITION_INDEPENDENT_CODE TRUE)
#set_target_properties(hdf5_local PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

# output to the ${CMAKE_SOURCE_DIR}
if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    set_target_properties(_kite PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR})
    foreach(config ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${config} config)
        set_target_properties(_kite PROPERTIES LIBRARY_OUTPUT_DIRECTORY_${config} ${CMAKE_SOURCE_DIR})
    endforeach()
endif()

add_custom_target(pytest COMMAND ${PYTHON_EXECUTABLE} -m pytest tests DEPENDS _kite
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})