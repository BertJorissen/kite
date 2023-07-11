set(PYBIND11_PYTHON_VERSION 3.8 CACHE STRING "Minimum required Python version")
add_subdirectory(deps/pybind11 EXCLUDE_FROM_ALL)

pybind11_add_module(kitecore src/main.cpp)

if(${DOWNLOAD_HDF5})
    MESSAGE("kitecore " ${hdf5_includes} ${hdf5_libs})
    add_dependencies(kitecore hdf5_local)
    target_include_directories(kitecore SYSTEM PRIVATE ${hdf5_includes})
    target_link_libraries(kitecore PRIVATE ${hdf5_libs})
else()
    target_include_directories(kitecore SYSTEM PRIVATE ${HDF5_INCLUDE_DIR})
    target_link_libraries(kitecore PRIVATE ${HDF5_CXX_LIBRARIES})

endif()
target_include_directories(kitecore SYSTEM PUBLIC ${EIGEN3_INCLUDE_DIR})

target_include_directories(kitecore SYSTEM PRIVATE ../cppcore/kitex/include)
target_include_directories(kitecore SYSTEM PRIVATE ../cppcore/kitetools/include)

target_link_libraries(kitecore PRIVATE cppcore_kitex)
target_link_libraries(kitecore PRIVATE cppcore_kitetools)

if(NOT MSVC)  # match default visibility of core library and extension module
    target_compile_options(cppcore_kitex PRIVATE -fvisibility=hidden)
    target_compile_options(cppcore_kitetools PRIVATE -fvisibility=hidden)
endif()

if(${OPENMP_FOUND})
    target_link_libraries(kitecore PRIVATE OpenMP::OpenMP_CXX)
    set(CORRECT_CODING_FLAGS "-Wall ")
    set(CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} -g -O3 ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -g -O3 ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS}")
else()
    set(CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_C_FLAGS}")
    set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -O3 ${CMAKE_CXX_FLAGS}")
    set(CMAKE_CXX_FLAGS_DEBUG "-g")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()


set_target_properties(cppcore_kitex PROPERTIES POSITION_INDEPENDENT_CODE TRUE)
set_target_properties(cppcore_kitetools PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

add_custom_command(TARGET kitecore
        POST_BUILD COMMAND
        ${CMAKE_INSTALL_NAME_TOOL} -add_rpath "@executable_path/../lib"
        $<TARGET_FILE:kitecore>)

# output to the ${CMAKE_SOURCE_DIR}
if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    set_target_properties(kitecore PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/kite/lib)
    foreach(config ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${config} config)
        set_target_properties(kitecore PROPERTIES LIBRARY_OUTPUT_DIRECTORY_${config} ${CMAKE_SOURCE_DIR}/kite/lib)
    endforeach()
endif()

add_custom_target(pytest COMMAND ${PYTHON_EXECUTABLE} -m pytest tests DEPENDS kitecore
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})