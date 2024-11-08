add_custom_target(docs COMMAND mkdocs build --site-dir ${CMAKE_CURRENT_BINARY_DIR}/html
        DEPENDS kitecore WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
