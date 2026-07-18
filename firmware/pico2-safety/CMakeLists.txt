cmake_minimum_required(VERSION 3.16)
project(rover_bean_safety_core C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_library(rover_bean_safety_core
    src/safety_core.c
    src/body_protocol.c
)
target_include_directories(rover_bean_safety_core PUBLIC include)
target_compile_options(rover_bean_safety_core PRIVATE -Wall -Wextra -Werror)

add_executable(test_safety_core tests/test_safety_core.c)
target_link_libraries(test_safety_core PRIVATE rover_bean_safety_core)
target_compile_options(test_safety_core PRIVATE -Wall -Wextra -Werror)

enable_testing()
add_test(NAME safety_core COMMAND test_safety_core)
