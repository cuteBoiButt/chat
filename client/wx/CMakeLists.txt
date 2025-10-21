cmake_minimum_required(VERSION 3.21)
project(SlightlyPrettyChatWxClient LANGUAGES CXX)

find_package(wxWidgets CONFIG REQUIRED)

add_executable(wx_client_app
    src/main.cpp
    src/graphicsContextManager.cpp
    src/cachedColorText.cpp
    src/appConfig.cpp
    src/authPanel.cpp
    src/chatPanel.cpp
    src/roomsPanel.cpp
    src/mainWidget.cpp
    src/wsClient.cpp
    src/messageWidget.cpp
    src/userListPanel.cpp
    src/textUtil.cpp
    src/userNameWidget.cpp
    src/messageView.cpp
    src/passwordUtil.cpp
    src/initialPanel.cpp
    src/serversPanel.cpp
    src/roomHeaderPanel.cpp
    src/roomSettingsPanel.cpp
    src/typingIndicatorPanel.cpp
    src/chatInterface.cpp
    src/accountSettings.cpp)

target_include_directories(wx_client_app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(wx_client_app PRIVATE
    common_lib
    wx::core
    wx::base
)

target_precompile_headers(wx_client_app PRIVATE
    "${CMAKE_SOURCE_DIR}/common/include/pch.h"
)

if(MSVC)
    target_link_options(wx_client_app PRIVATE "/SUBSYSTEM:WINDOWS")
endif()

if(NOT APPLE)
    # This command is for local execution on Windows/Linux, not for macOS bundles.
    add_custom_command(
        TARGET wx_client_app POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory_if_different
                "${CMAKE_CURRENT_SOURCE_DIR}/fonts"
                "$<TARGET_FILE_DIR:wx_client_app>/fonts"
        COMMENT "Copying fonts for local execution..."
    )
endif()

file(GLOB FONT_FILES "${CMAKE_CURRENT_SOURCE_DIR}/fonts/*.ttf")

# --- Application Installation and Bundling ---

if(APPLE)
    # On macOS, we bundle resources directly into the .app package.
    # First, add the font files as resource-type sources to the target.
    target_sources(wx_client_app PRIVATE ${FONT_FILES})

    # Tell CMake to place these specific source files into the
    # "Contents/Resources/fonts" directory inside the .app bundle.
    set_source_files_properties(${FONT_FILES}
        PROPERTIES MACOSX_PACKAGE_LOCATION "Resources/Fonts"
    )

    # This creates the .app structure and automatically includes the
    # resources we just configured.
    set_target_properties(wx_client_app PROPERTIES
        MACOSX_BUNDLE TRUE

        # Sets CFBundleName from the top-level CPack variable
        MACOSX_BUNDLE_BUNDLE_NAME "${CPACK_PACKAGE_NAME}"

        # Sets CFBundleIdentifier. This must be a unique string.
        MACOSX_BUNDLE_GUI_IDENTIFIER "com.yourname.slightlyprettychat.wx"

        # Sets CFBundleVersion from the top-level CPack variable
        MACOSX_BUNDLE_BUNDLE_VERSION "${CPACK_PACKAGE_VERSION}"

        # Sets CFBundleShortVersionString from the top-level CPack variable
        MACOSX_BUNDLE_SHORT_VERSION_STRING "${CPACK_PACKAGE_VERSION}"
    )
    install(TARGETS wx_client_app BUNDLE DESTINATION . COMPONENT wx_client)
else()
    # For Windows and Linux, we install the executable...
    install(TARGETS wx_client_app DESTINATION . COMPONENT wx_client)
    # ...and then install the fonts directory alongside it.
    install(
        DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/fonts/"
        DESTINATION "fonts"
        COMPONENT wx_client
    )
endif()

if(WIN32)
    # The Windows fixup is needed because vcpkg defaults to
    # dynamic linking on Windows.
    install(CODE "
        include(BundleUtilities)
        fixup_bundle(\"\${CMAKE_INSTALL_PREFIX}/wx_client_app.exe\" \"\" \"$<TARGET_FILE_DIR:wx_client_app>\")
    " COMPONENT wx_client)
endif()

if(LINUX) 
    include(${CMAKE_SOURCE_DIR}/cmake/AppImage.cmake)

    add_appimage_from_component(
        COMPONENT_NAME "wx_client"
        DISPLAY_NAME "Slightly Pretty Chat Wx"
        EXECUTABLE_NAME "wx_client_app"
        PLUGIN_TYPE gtk
    )
endif()
