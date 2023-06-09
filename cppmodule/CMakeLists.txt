set(PYBIND11_PYTHON_VERSION 3.5 CACHE STRING "Minimum required Python version")
add_subdirectory(deps/pybind11 EXCLUDE_FROM_ALL)

pybind11_add_module(_kite
        src/main.cpp)

target_include_directories(_kite PRIVATE ../cppcore/kitex/include)
target_include_directories(_kite PRIVATE ../cppcore/kitetools/include)

target_link_libraries(_kite PRIVATE cppcore_kitex)
target_link_libraries(_kite PRIVATE cppcore_kitetools)


if(NOT MSVC)  # match default visibility of core library and extension module
    target_compile_options(cppcore_kitex PUBLIC -fvisibility=hidden)
    target_compile_options(cppcore_kitetools PUBLIC -fvisibility=hidden)
endif()

set_target_properties(cppcore_kitex PROPERTIES POSITION_INDEPENDENT_CODE TRUE)
set_target_properties(cppcore_kitetools PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

# output to the ${CMAKE_SOURCE_DIR}
if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    set_target_properties(_kite PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR})
    foreach(config ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${config} config)
        set_target_properties(_kite PROPERTIES LIBRARY_OUTPUT_DIRECTORY_${config} ${CMAKE_SOURCE_DIR})
    endforeach()
endif()