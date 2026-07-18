cmake_minimum_required(VERSION 3.16)

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(rover_bean_pico2_safety C CXX ASM)
pico_sdk_init()

add_executable(rover_bean_pico2_safety
    ../src/pico_main.c
    ../src/safety_core.c
    ../src/body_protocol.c
)
target_include_directories(rover_bean_pico2_safety PRIVATE ../include)
target_compile_definitions(rover_bean_pico2_safety PRIVATE RB_HARDWARE_RELEASE=0)
target_link_libraries(rover_bean_pico2_safety PRIVATE pico_stdlib hardware_uart hardware_pwm hardware_adc)
pico_enable_stdio_usb(rover_bean_pico2_safety 0)
pico_enable_stdio_uart(rover_bean_pico2_safety 0)
pico_add_extra_outputs(rover_bean_pico2_safety)
