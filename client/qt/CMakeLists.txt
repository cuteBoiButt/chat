cmake_minimum_required(VERSION 3.21)
project(SlightlyPrettyChatQtClient LANGUAGES CXX)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

set(CMAKE_AUTOUIC_SEARCH_PATHS ${CMAKE_CURRENT_SOURCE_DIR}/forms)

find_package(Qt6 REQUIRED COMPONENTS Core Widgets Gui Qml Quick QuickWidgets)

set(QML_PATH_FROM_ENV "$ENV{QML2_IMPORT_PATH}")
if(QML_PATH_FROM_ENV AND EXISTS "${QML_PATH_FROM_ENV}")
    set(QMLLS_INI_CONTENT "[General]\nimportPaths = ${QML_PATH_FROM_ENV}\n")
    file(WRITE "${PROJECT_BINARY_DIR}/.qmlls.ini" "${QMLLS_INI_CONTENT}")
    message(STATUS "Generated .qmlls.ini from environment variable in ${PROJECT_BINARY_DIR}")
else()
    message(WARNING "ENV{QML2_IMPORT_PATH} not found or invalid. .qmlls.ini not generated.")
endif()

add_executable(qt_client_app
    src/main.cpp

    src/backend/backend.cpp
    include/backend/backend.h

    src/ui/mainwindow.cpp
    include/ui/mainwindow.h

    src/ui/connectwidget.cpp
    include/ui/connectwidget.h

    src/ui/loginscreen.cpp
    include/ui/loginscreen.h

    resources.qrc
)

target_include_directories(qt_client_app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

target_link_libraries(qt_client_app PRIVATE 
        common_lib 
        Qt6::Core
        Qt6::Gui
        Qt6::Qml
        Qt6::Quick
        Qt6::QuickWidgets
        Qt6::Widgets
)

if(WIN32)
    # Find windeployqt
    get_target_property(QT_QMAKE_EXECUTABLE Qt6::qmake IMPORTED_LOCATION)
    get_filename_component(QT_BIN_DIR "${QT_QMAKE_EXECUTABLE}" DIRECTORY)
    set(WINDEPLOYQT_EXECUTABLE "${QT_BIN_DIR}/windeployqt.exe")

    install(
        TARGETS qt_client_app
        DESTINATION .
        COMPONENT qt_client
    )

    install(CODE "
        execute_process(
            COMMAND \"${WINDEPLOYQT_EXECUTABLE}\" 
                    \"\${CMAKE_INSTALL_PREFIX}/qt_client_app.exe\"
                    --dir \"\${CMAKE_INSTALL_PREFIX}\"
                    --qmldir \"${CMAKE_CURRENT_SOURCE_DIR}/qml\"
        )
    " COMPONENT qt_client)

elseif(APPLE)
    # This creates the .app structure and automatically includes the
    # resources
    set_target_properties(qt_client_app PROPERTIES
        MACOSX_BUNDLE TRUE

        # Sets CFBundleName from the top-level CPack variable
        MACOSX_BUNDLE_BUNDLE_NAME "${CPACK_PACKAGE_NAME}"

        # Sets CFBundleIdentifier. This must be a unique string.
        MACOSX_BUNDLE_GUI_IDENTIFIER "com.yourname.slightlyprettychat.qt"

        # Sets CFBundleVersion from the top-level CPack variable
        MACOSX_BUNDLE_BUNDLE_VERSION "${CPACK_PACKAGE_VERSION}"

        # Sets CFBundleShortVersionString from the top-level CPack variable
        MACOSX_BUNDLE_SHORT_VERSION_STRING "${CPACK_PACKAGE_VERSION}"
    )
    install(TARGETS qt_client_app BUNDLE DESTINATION . COMPONENT qt_client)

    # Find macdeployqt
    get_target_property(QT_QMAKE_EXECUTABLE Qt6::qmake IMPORTED_LOCATION)
    get_filename_component(QT_BIN_DIR "${QT_QMAKE_EXECUTABLE}" DIRECTORY)
    set(MACDEPLOYQT_EXECUTABLE "${QT_BIN_DIR}/macdeployqt")

    install(CODE "
        execute_process(
            COMMAND \"${MACDEPLOYQT_EXECUTABLE}\" 
                    \"\${CMAKE_INSTALL_PREFIX}/qt_client_app.app\"
                    -always-overwrite
                    -qmldir=${CMAKE_CURRENT_SOURCE_DIR}/qml
                    -verbose=1
        )
    " COMPONENT qt_client)

else() # LINUX
    include(${CMAKE_SOURCE_DIR}/cmake/AppImage.cmake)

    install(
        TARGETS qt_client_app
        DESTINATION .
        COMPONENT qt_client
    )

    add_appimage_from_component(
        COMPONENT_NAME "qt_client"
        DISPLAY_NAME "Slightly Pretty Chat Qt"
        EXECUTABLE_NAME "qt_client_app"
        PLUGIN_TYPE qt
        EXTRA_ENV_VARS
            "QML_SOURCES_PATHS=${CMAKE_CURRENT_SOURCE_DIR}/qml"
            "EXTRA_QT_PLUGINS=waylandcompositor<SEMICOLON>qml"
            "EXTRA_PLATFORM_PLUGINS=libqwayland.so"
    )
endif()
