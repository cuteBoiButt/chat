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

install(
    TARGETS qt_client_app
    DESTINATION .
    COMPONENT qt_client
)
install(
    DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/qml/
    DESTINATION qml
    COMPONENT qt_client
)

