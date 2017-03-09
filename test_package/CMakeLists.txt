cmake_minimum_required(VERSION 2.8)

project(TestZlib C CXX)

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

add_executable(main_c main.c)
add_executable(main_cpp main.cpp)

if(CMAKE_VERSION VERSION_LESS 3.1.2)
target_link_libraries(main_c ${CONAN_LIBS})
target_link_libraries(main_cpp ${CONAN_LIBS})
else()
target_link_libraries(main_c CONAN_PKG::zlib)
target_link_libraries(main_cpp CONAN_PKG::zlib)
endif()

if(CMAKE_VERSION VERSION_LESS 3.1)
set_target_properties(main_c PROPERTIES
    COMPILE_OPTIONS "-std=c11"
)
set_target_properties(main_cpp PROPERTIES
    COMPILE_OPTIONS "-std=c++11"
)
else()
set_target_properties(main_c PROPERTIES
    C_EXTENSIONS OFF
    C_STANDARD 11
    C_STANDARD_REQUIRED ON
)
set_target_properties(main_cpp PROPERTIES
    CXX_EXTENSIONS OFF
    CXX_STANDARD 11
    CXX_STANDARD_REQUIRED ON
)
endif()

if(APPLE)
set_property(TARGET main_c APPEND PROPERTY INSTALL_RPATH "@executable_path/../lib")
set_property(TARGET main_cpp APPEND PROPERTY INSTALL_RPATH "@executable_path/../lib")
elseif(WIN32)
# No @rpath on Windows.
else()
set_property(TARGET main_c APPEND PROPERTY INSTALL_RPATH "\$ORIGIN/../lib")
set_property(TARGET main_cpp APPEND PROPERTY INSTALL_RPATH "\$ORIGIN/../lib")
endif()

enable_testing()

add_test(NAME print_zlib_version_c COMMAND main_c)
set_tests_properties(print_zlib_version_c PROPERTIES
    PASS_REGULAR_EXPRESSION "zlib 1.2.11"
)

add_test(NAME print_zlib_version_cpp COMMAND main_cpp)
set_tests_properties(print_zlib_version_cpp PROPERTIES
    PASS_REGULAR_EXPRESSION "zlib 1.2.11"
)
