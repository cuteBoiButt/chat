cmake_minimum_required(VERSION 3.21)
project(SlightlyPrettyChatQtClient LANGUAGES CXX)

set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Widgets)

add_executable(qt_client_app main.cpp)

target_link_libraries(qt_client_app 
    PRIVATE 
        common_lib 
        Qt6::Widgets
)

install(TARGETS qt_client_app DESTINATION . COMPONENT qt_client)
