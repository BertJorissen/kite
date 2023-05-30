set(CMAKE_CXX_STANDARD 17)

add_subdirectory(deps/pybind11)
pybind11_add_module(_kite src/main.cpp)

target_link_libraries(_kite PRIVATE kitecpp)
target_link_libraries(_kite PRIVATE kitetoolscpp)

set_target_properties(kitecpp PROPERTIES POSITION_INDEPENDENT_CODE TRUE)
set_target_properties(kitetoolscpp PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

# output to the ${CMAKE_SOURCE_DIR}
if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    set_target_properties(_kite PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR})
    foreach(config ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${config} config)
        set_target_properties(_kite PROPERTIES
                LIBRARY_OUTPUT_DIRECTORY_${config} ${CMAKE_SOURCE_DIR})
    endforeach()
endif()