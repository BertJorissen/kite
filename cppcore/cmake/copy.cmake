if(${HDF5_MOVE_FILES} STREQUAL "TRUE")
    # Find files matching the pattern "libhdf5.so*"
    file(GLOB HDF5_LIBRARY_FILES "${HDF5_DIR}/build/libhdf5.so*")

    # Find files matching the pattern "libhdf5_cpp.so*"
    file(GLOB HDF5_CPP_LIBRARY_FILES "${HDF5_DIR}/build/libhdf5_cpp.so*")

    # Concatenate the file lists
    set(ALL_LIBRARY_FILES ${HDF5_LIBRARY_FILES} ${HDF5_CPP_LIBRARY_FILES})

    # Copy the files to the destination directory
    file(COPY ${ALL_LIBRARY_FILES} DESTINATION "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")

    MESSAGE(${ALL_LIBRARY_FILES}-${HDF5_DIR}-${CMAKE_LIBRARY_OUTPUT_DIRECTORY}-HDF5_MOVE_FILES)
endif()