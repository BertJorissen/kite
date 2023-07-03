if(${HDF5_MOVE_FILES} STREQUAL "TRUE")
    # Find files matching the pattern "libhdf5.so*"
    file(GLOB HDF5_LIBRARY_FILES "${HDF5_DIR}/build/bin/libhdf5.*${HDF_SL_EXT}*")

    # Find files matching the pattern "libhdf5_cpp.so*"
    file(GLOB HDF5_CPP_LIBRARY_FILES "${HDF5_DIR}/build/bin/libhdf5_cpp.*${HDF_SL_EXT}*")

    # Concatenate the file lists
    set(ALL_LIBRARY_FILES ${HDF5_LIBRARY_FILES} ${HDF5_CPP_LIBRARY_FILES})

    # Copy the files to the destination directory
    file(COPY ${ALL_LIBRARY_FILES} DESTINATION "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")

    # see if moved
    file(GLOB moved "${HDF5_DIR}/build/bin/*")

    MESSAGE(${ALL_LIBRARY_FILES}-${HDF5_DIR}-${CMAKE_LIBRARY_OUTPUT_DIRECTORY}-${moved}-${HDF_SL_EXT}-HDF5_MOVE_FILES)
endif()