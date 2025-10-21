# cmake/LinuxDeployAppImage.cmake
# This script runs during CPack to create AppImages

message(STATUS "[DEBUG LinuxDeployAppImage.cmake] Received EXTRA_ENV_VARS = [${EXTRA_ENV_VARS}]")

if(NOT DEFINED COMPONENT_NAME)
    message(FATAL_ERROR "COMPONENT_NAME must be defined")
endif()

if(NOT DEFINED APP_NAME)
    message(FATAL_ERROR "APP_NAME must be defined")
endif()

if(NOT DEFINED EXECUTABLE_NAME)
    message(FATAL_ERROR "EXECUTABLE_NAME must be defined")
endif()

if(NOT DEFINED PLUGIN_TYPE)
    set(PLUGIN_TYPE "qt") # default to qt
endif()

set(APPDIR "${CMAKE_CURRENT_BINARY_DIR}/AppDir_${COMPONENT_NAME}")
set(LINUXDEPLOY_DIR "${CMAKE_CURRENT_BINARY_DIR}/linuxdeploy_tools")

# Reusable function to download and extract AppImages
function(ensure_appimage_tool TOOL_NAME DOWNLOAD_URL)
    set(TOOL_PATH "${LINUXDEPLOY_DIR}/${TOOL_NAME}")
    
    if(EXISTS "${TOOL_PATH}")
        return()
    endif()
    
    file(MAKE_DIRECTORY "${LINUXDEPLOY_DIR}")
    
    message(STATUS "Downloading ${TOOL_NAME}...")
    file(DOWNLOAD 
        "${DOWNLOAD_URL}"
        "${TOOL_PATH}.tmp"
        SHOW_PROGRESS
    )
    
    execute_process(
        COMMAND chmod +x "${TOOL_PATH}.tmp"
    )
    
    execute_process(
        COMMAND "${TOOL_PATH}.tmp" --appimage-extract
        WORKING_DIRECTORY "${LINUXDEPLOY_DIR}"
        RESULT_VARIABLE EXTRACT_RESULT
    )
    
    if(NOT EXTRACT_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to extract ${TOOL_NAME}")
    endif()
    
    file(RENAME 
        "${LINUXDEPLOY_DIR}/squashfs-root" 
        "${LINUXDEPLOY_DIR}/${TOOL_NAME}-squashfs-root"
    )
    
    file(CREATE_LINK 
        "${LINUXDEPLOY_DIR}/${TOOL_NAME}-squashfs-root/AppRun"
        "${TOOL_PATH}"
        SYMBOLIC
    )
    
    file(REMOVE "${TOOL_PATH}.tmp")
    
    message(STATUS "${TOOL_NAME} ready")
endfunction()

# Reusable function to download shell scripts
function(ensure_shell_script SCRIPT_NAME DOWNLOAD_URL)
    set(SCRIPT_PATH "${LINUXDEPLOY_DIR}/${SCRIPT_NAME}")
    
    if(EXISTS "${SCRIPT_PATH}")
        return()
    endif()
    
    file(MAKE_DIRECTORY "${LINUXDEPLOY_DIR}")
    
    message(STATUS "Downloading ${SCRIPT_NAME}...")
    file(DOWNLOAD 
        "${DOWNLOAD_URL}"
        "${SCRIPT_PATH}"
        SHOW_PROGRESS
    )
    
    execute_process(
        COMMAND chmod +x "${SCRIPT_PATH}"
    )
    
    message(STATUS "${SCRIPT_NAME} ready")
endfunction()

# Clean up previous AppDir
file(REMOVE_RECURSE "${APPDIR}")

# Install component to AppDir
execute_process(
    COMMAND ${CMAKE_COMMAND} --install . --config Release 
            --component ${COMPONENT_NAME} --prefix ${APPDIR}/usr/bin
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    RESULT_VARIABLE INSTALL_RESULT
)

if(NOT INSTALL_RESULT EQUAL 0)
    message(FATAL_ERROR "Failed to install component ${COMPONENT_NAME}")
endif()

# Create .desktop file
file(MAKE_DIRECTORY "${APPDIR}/usr/share/applications")
set(DESKTOP_CONTENT "[Desktop Entry]
Type=Application
Name=${APP_NAME}
Exec=${EXECUTABLE_NAME}
Categories=Utility;
Icon=appname
")
file(WRITE "${APPDIR}/usr/share/applications/${EXECUTABLE_NAME}.desktop" "${DESKTOP_CONTENT}")

# Create icon placeholder
file(MAKE_DIRECTORY "${APPDIR}/usr/share/icons/hicolor/scalable/apps")
file(TOUCH "${APPDIR}/usr/share/icons/hicolor/scalable/apps/appname.svg")

# Ensure linuxdeploy is available
ensure_appimage_tool(
    "linuxdeploy-x86_64.AppImage"
    "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
)

# Setup plugin based on type
if(PLUGIN_TYPE STREQUAL "qt")
    ensure_appimage_tool(
        "linuxdeploy-plugin-qt-x86_64.AppImage"
        "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/1-alpha-20250213-1/linuxdeploy-plugin-qt-x86_64.AppImage"
    )
elseif(PLUGIN_TYPE STREQUAL "gtk")
    ensure_shell_script(
        "linuxdeploy-plugin-gtk.sh"
        "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh"
    )
    
    # Apply patch for libgtk-3-0t64
    file(READ "${LINUXDEPLOY_DIR}/linuxdeploy-plugin-gtk.sh" PLUGIN_CONTENT)
    string(REPLACE "libgtk-3-0" "libgtk-3-0t64" PLUGIN_CONTENT "${PLUGIN_CONTENT}")
    file(WRITE "${LINUXDEPLOY_DIR}/linuxdeploy-plugin-gtk.sh" "${PLUGIN_CONTENT}")
endif()

# Prepare environment: add LINUXDEPLOY_DIR to PATH so plugins can be found
set(LINUXDEPLOY_ENV "PATH=${LINUXDEPLOY_DIR}:$ENV{PATH}")

# Parse EXTRA_ENV_VARS if provided (split by our custom delimiter)
if(DEFINED EXTRA_ENV_VARS AND NOT EXTRA_ENV_VARS STREQUAL "")
    foreach(ENV_VAR IN LISTS EXTRA_ENV_VARS)
        string(REPLACE "<SEMICOLON>" "\\;" ENV_VAR "${ENV_VAR}")
        message(STATUS "[DEBUG] Adding env var: ${ENV_VAR}")
        list(APPEND LINUXDEPLOY_ENV "${ENV_VAR}")
    endforeach()
endif()

message(STATUS "[DEBUG] Final LINUXDEPLOY_ENV list:")
foreach(ENV_VAR IN LISTS LINUXDEPLOY_ENV)
    message(STATUS "    ${ENV_VAR}")
endforeach()

# Run linuxdeploy
message(STATUS "Running linuxdeploy for ${COMPONENT_NAME}...")
execute_process(
    COMMAND ${CMAKE_COMMAND} -E env ${LINUXDEPLOY_ENV}
            ${LINUXDEPLOY_DIR}/linuxdeploy-x86_64.AppImage 
            --appdir ${APPDIR} 
            --plugin ${PLUGIN_TYPE}
            --output appimage
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    RESULT_VARIABLE LINUXDEPLOY_RESULT
)

if(NOT LINUXDEPLOY_RESULT EQUAL 0)
    message(FATAL_ERROR "linuxdeploy failed for ${COMPONENT_NAME}")
endif()

message(STATUS "AppImage created successfully for ${COMPONENT_NAME}")
