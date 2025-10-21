# This script provides a reusable function to create an AppImage from a pre-defined component.

include(CMakeParseArguments)

#[[
# Configures the necessary targets and install rules to generate an AppImage
# from a component during the 'package' step.
#
# The caller is responsible for defining the component and installing all
# necessary files (executables, data, fonts, etc.) into it.
#
# Usage:
# add_appimage_from_component(
#     COMPONENT_NAME <name>           # The pre-defined component to package
#     DISPLAY_NAME "<display_name>"   # The user-facing name for the app
#     EXECUTABLE_NAME <exec_name>     # The main executable in the component for the .desktop file
#     [PLUGIN_TYPE <qt|gtk>]          # The linuxdeploy plugin to use (default: qt)
#     [EXTRA_ENV_VARS <var1> <var2>...] # Optional list of "KEY=VALUE" environment variables
# )
#]]
function(add_appimage_from_component)
    # 1. Define and parse the function's arguments
    set(options "")
    set(one_value_keywords COMPONENT_NAME DISPLAY_NAME EXECUTABLE_NAME PLUGIN_TYPE)
    set(multi_value_keywords EXTRA_ENV_VARS)
    cmake_parse_arguments(ARG "${options}" "${one_value_keywords}" "${multi_value_keywords}" ${ARGN})

    # Validate required arguments
    if(NOT DEFINED ARG_COMPONENT_NAME)
        message(FATAL_ERROR "add_appimage_from_component: COMPONENT_NAME is required.")
    endif()
    if(NOT DEFINED ARG_DISPLAY_NAME)
        message(FATAL_ERROR "add_appimage_from_component: DISPLAY_NAME is required.")
    endif()
    if(NOT DEFINED ARG_EXECUTABLE_NAME)
        message(FATAL_ERROR "add_appimage_from_component: EXECUTABLE_NAME is required.")
    endif()

    # Set default values for optional arguments
    if(NOT DEFINED ARG_PLUGIN_TYPE)
        set(ARG_PLUGIN_TYPE "qt")
    endif()

    # 2. Define unique names for this AppImage task.
    #    CRITICAL: Sanitize the display name to match linuxdeploy's output behavior
    #    by replacing spaces with underscores. This ensures the file path we
    #    use matches the file that is actually created.
    string(REPLACE " " "_" sanitized_name "${ARG_DISPLAY_NAME}")
    set(appimage_file_name "${sanitized_name}-x86_64.AppImage")
    set(appimage_full_path "${CMAKE_BINARY_DIR}/${appimage_file_name}")

    set(custom_target_name "create_appimage_${ARG_COMPONENT_NAME}")
    set(package_component_name "${ARG_COMPONENT_NAME}_package")

    # 3. Define the command that generates the AppImage file
    set(linuxdeploy_args
        -DCOMPONENT_NAME=${ARG_COMPONENT_NAME}
        -DAPP_NAME=${ARG_DISPLAY_NAME}
        -DEXECUTABLE_NAME=${ARG_EXECUTABLE_NAME}
        -DPLUGIN_TYPE=${ARG_PLUGIN_TYPE}
        -DCMAKE_CURRENT_BINARY_DIR=${CMAKE_BINARY_DIR}
    )

    if(ARG_EXTRA_ENV_VARS)
        string(JOIN ";" env_vars_string "${ARG_EXTRA_ENV_VARS}")
        string(REPLACE ";" "\\;" env_vars_string "${env_vars_string}")
        list(APPEND linuxdeploy_args "-DEXTRA_ENV_VARS:STRING=\"${env_vars_string}\"")
    endif()

    list(APPEND linuxdeploy_args "-P" "${CMAKE_SOURCE_DIR}/cmake/LinuxDeployAppImage.cmake")

    message(STATUS "[DEBUG AppImage.cmake] Arguments list being passed to add_custom_command:")
    foreach(arg IN LISTS linuxdeploy_args)
        message(STATUS "    ${arg}")
    endforeach()

    add_custom_command(
        OUTPUT "${appimage_full_path}"
        COMMAND ${CMAKE_COMMAND} ${linuxdeploy_args}
        DEPENDS ${ARG_EXECUTABLE_NAME}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        COMMENT "Defining how to generate AppImage for component '${ARG_COMPONENT_NAME}'"
    )

    # Create a unique custom target to trigger the command
    add_custom_target(${custom_target_name} DEPENDS "${appimage_full_path}")

    # 4. During the 'package' step, build the AppImage and then install it
    install(
        CODE "
            message(STATUS \"Packaging: Building AppImage for component '${ARG_COMPONENT_NAME}' in '\${CMAKE_INSTALL_CONFIG_NAME}' config...\")
            execute_process(
                COMMAND \"${CMAKE_COMMAND}\" --build \"${CMAKE_BINARY_DIR}\" --target ${custom_target_name} --config \"\${CMAKE_INSTALL_CONFIG_NAME}\"
                RESULT_VARIABLE result
            )
            if(NOT result EQUAL 0)
                message(FATAL_ERROR \"Failed to build AppImage for component '${ARG_COMPONENT_NAME}'.\")
            endif()
        "
        COMPONENT ${package_component_name}
    )

    install(
        FILES "${appimage_full_path}"
        DESTINATION .
        COMPONENT ${package_component_name}
    )
endfunction()
