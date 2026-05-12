cmake_minimum_required(VERSION 3.10)
project(AuthSystem VERSION 1.0 LANGUAGES CXX)

message(STATUS "========================================")
message(STATUS " DevPal C++ Authentication System")
message(STATUS " Version: ${PROJECT_VERSION}")
message(STATUS "========================================")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")

if(MSVC)
    message(STATUS "Compiler: MSVC")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /O2 /MD /W2")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /Od /MDd /W2 /Zi")
else()
    message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

include_directories(${PROJECT_SOURCE_DIR}/include)

# Build library
file(GLOB SOURCES src/*.cpp)
list(REMOVE_ITEM SOURCES ${PROJECT_SOURCE_DIR}/src/main.cpp)
add_library(auth_lib STATIC ${SOURCES})

# Main executable
add_executable(auth_system src/main.cpp)
target_link_libraries(auth_system PRIVATE auth_lib)

# Test executable
enable_testing()
add_executable(test_auth tests/test_auth.cpp)
target_link_libraries(test_auth PRIVATE auth_lib)
add_test(NAME AuthSystemTests COMMAND test_auth)

message(STATUS "========================================")
message(STATUS " Configuration complete!")
message(STATUS " - auth_system: Main executable")
message(STATUS " - test_auth: Test executable")
message(STATUS "========================================")
