set(PYBIND11_PYTHON_VERSION 3.9 CACHE STRING "Minimum required Python version")
set(PYBIND11_FINDPYTHON ON)
add_subdirectory(deps/pybind11 EXCLUDE_FROM_ALL)

pybind11_add_module(kitecore THIN_LTO src/main.cpp)

if(${DOWNLOAD_HDF5})
    add_dependencies(kitecore hdf5_local cppcore_kitex cppcore_kitetools)
    target_include_directories(kitecore SYSTEM PRIVATE ${hdf5_includes})
    target_link_libraries(kitecore PRIVATE ${hdf5_libs})
else()
    target_include_directories(kitecore SYSTEM PRIVATE ${HDF5_INCLUDE_DIR})
    target_link_libraries(kitecore PRIVATE ${HDF5_CXX_LIBRARIES})
    add_dependencies(kitecore cppcore_kitex cppcore_kitetools)
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
set_target_properties(cppcore_kitex PROPERTIES POSITION_INDEPENDENT_CODE TRUE)
set_target_properties(cppcore_kitetools PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

if(${DOWNLOAD_OPENMP}) # failed to find OPENMP, so install it
    MESSAGE(FATAL_ERROR "no download yet")
    #add_dependencies(kitecore openmp_local)
    #target_include_directories(kitecore SYSTEM PRIVATE ${OPENMP_includes})
    #target_link_libraries(kitecore PRIVATE ${OPENMP_libs})
    #MESSAGE(STATUS "Using downloaded HDF5 for KITE-tools with includes ${OPENMP_includes} and libs ${OPENMP_libs}")
else()
    message(STATUS "kitecore - OpenMP")
    target_link_libraries(kitecore PRIVATE OpenMP::OpenMP_CXX)
    set(CORRECT_CODING_FLAGS "-Wall -DH5_BUILT_AS_DYNAMIC_LIB")
    if(MSVC)
        set(CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
        set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    else()
        set(CMAKE_C_FLAGS "${CORRECT_CODING_FLAGS} -g -O3 ${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
        set(CMAKE_CXX_FLAGS "${CORRECT_CODING_FLAGS} -g -O3 ${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    endif()
    set(CMAKE_EXE_LINKER_FLAGS "${CORRECT_CODING_FLAGS} ${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS}")
endif()

if ("${CMAKE_CXX_COMPILER_ID}" MATCHES ".*Clang.*")  # similar as in the first parts; don't ask me why this works lol
    add_custom_command(TARGET kitecore
            POST_BUILD COMMAND
            ${CMAKE_INSTALL_NAME_TOOL} -add_rpath "@loader_path"
            $<TARGET_FILE:kitecore>)
endif()

# output to the ${CMAKE_SOURCE_DIR}
if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    set_target_properties(kitecore PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/kite/lib)
    foreach(config ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${config} config)
        set_target_properties(kitecore PROPERTIES LIBRARY_OUTPUT_DIRECTORY_${config} ${CMAKE_SOURCE_DIR}/kite/lib)
    endforeach()
endif()

add_custom_target(pytest COMMAND ${PYTHON_EXECUTABLE} -m pytest DEPENDS kitecore
                  WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
