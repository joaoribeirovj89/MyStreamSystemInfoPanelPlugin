cmake_minimum_required(VERSION 3.20)

project(MyStreamSystemInfoPanelPlugin LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(MYSTREAM_PLUGIN_ID "mystream_system_info_panel" CACHE STRING "Plugin package id")
set(MYSTREAM_PLUGIN_NAME "System Info Panel" CACHE STRING "Plugin display name")
set(MYSTREAM_PLUGIN_VERSION "0.1.1" CACHE STRING "Plugin version")
set(MYSTREAM_PLUGIN_CATEGORY "Panel" CACHE STRING "Plugin category")
set(MYSTREAM_PLUGIN_TARGET "mystream_system_info_panel" CACHE STRING "Plugin target/output name")
set(MYSTREAM_PLUGIN_API_VERSION "28" CACHE STRING "MyStream plugin API version")
set(MYSTREAM_PLUGIN_SDK_VERSION "0.2.0" CACHE STRING "SDK version used to build this plugin")
set(MYSTREAM_PLUGIN_SDK_MIN_VERSION "0.2.0" CACHE STRING "Minimum compatible MyStream SDK version")
set(MYSTREAM_PLUGIN_SDK_MAX_VERSION "0.3.0" CACHE STRING "Exclusive maximum compatible MyStream SDK version")
set(MYSTREAM_PLUGIN_SDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/sdk" CACHE PATH "Path to MyStreamPluginSDK")

if(NOT EXISTS "${MYSTREAM_PLUGIN_SDK_DIR}/include/mystream/plugin_sdk.hpp")
    message(FATAL_ERROR "MyStreamPluginSDK not found. Set MYSTREAM_PLUGIN_SDK_DIR to its repository root.")
endif()

add_subdirectory(
    "${MYSTREAM_PLUGIN_SDK_DIR}"
    "${CMAKE_BINARY_DIR}/mystream-plugin-sdk")

add_library(${MYSTREAM_PLUGIN_TARGET} SHARED src/panel_plugin.cpp)
target_include_directories(${MYSTREAM_PLUGIN_TARGET} PRIVATE "${MYSTREAM_PLUGIN_SDK_DIR}/include")

target_link_libraries(${MYSTREAM_PLUGIN_TARGET} PRIVATE MyStream::PluginSDK)

set(MYSTREAM_PLUGIN_PACKAGE_DIR "${CMAKE_BINARY_DIR}/${MYSTREAM_PLUGIN_TARGET}")
set_target_properties(${MYSTREAM_PLUGIN_TARGET} PROPERTIES
    OUTPUT_NAME "${MYSTREAM_PLUGIN_TARGET}"
    LIBRARY_OUTPUT_DIRECTORY "${MYSTREAM_PLUGIN_PACKAGE_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${MYSTREAM_PLUGIN_PACKAGE_DIR}"
)

file(GENERATE
    OUTPUT "${MYSTREAM_PLUGIN_PACKAGE_DIR}/mystream-plugin.manifest"
    CONTENT "format=1
id=${MYSTREAM_PLUGIN_ID}
name=${MYSTREAM_PLUGIN_NAME}
version=${MYSTREAM_PLUGIN_VERSION}
category=${MYSTREAM_PLUGIN_CATEGORY}
library=$<TARGET_FILE_NAME:${MYSTREAM_PLUGIN_TARGET}>
plugin_api_version=${MYSTREAM_PLUGIN_API_VERSION}
sdk_version=${MYSTREAM_PLUGIN_SDK_VERSION}
sdk_min_version=${MYSTREAM_PLUGIN_SDK_MIN_VERSION}
sdk_max_version=${MYSTREAM_PLUGIN_SDK_MAX_VERSION}
")
