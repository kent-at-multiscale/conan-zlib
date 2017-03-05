cmake_minimum_required(VERSION 2.8)

if(CMAKE_VERSION VERSION_LESS 3.0)
project(TestZlib C CXX)
else()
project(TestZlib LANGUAGES CXX)
endif()

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
if(CMAKE_VERSION VERSION_LESS 3.1.2)
conan_basic_setup()
else()
conan_basic_setup(TARGETS)
endif()

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CMAKE_SKIP_RPATH OFF)
set(CMAKE_MACOSX_RPATH ON)
set(CMAKE_SKIP_BUILD_RPATH ON)
set(CMAKE_SKIP_INSTALL_RPATH OFF)
set(CMAKE_BUILD_WITH_INSTALL_RPATH ON)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH OFF)

find_package("ZLIB" 1.2.11 EXACT REQUIRED)

add_executable(main main.cpp)

if(CMAKE_VERSION VERSION_LESS 3.1)
set_target_properties(main PROPERTIES
    COMPILE_OPTIONS "-std=c++11"
)
else()
set_target_properties(main PROPERTIES
    CXX_EXTENSIONS OFF
    CXX_STANDARD 11
    CXX_STANDARD_REQUIRED ON
)
endif()

if(APPLE)
set_property(TARGET main APPEND PROPERTY INSTALL_RPATH "@executable_path/../lib")
elseif(WIN32)
# No @rpath on Windows.
else()
set_property(TARGET main APPEND PROPERTY INSTALL_RPATH "\$ORIGIN/../lib")
endif()

target_include_directories(main PRIVATE ${ZLIB_INCLUDE_DIRS})
target_link_libraries(main ${ZLIB_LIBRARIES})

enable_testing()

add_test(NAME print_zlib_version COMMAND main)
set_tests_properties(print_zlib_version PROPERTIES
    PASS_REGULAR_EXPRESSION "zlib 1.2.11"
)
