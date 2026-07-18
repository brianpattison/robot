#ifndef ROVER_BEAN_SAFETY_CORE_H
#define ROVER_BEAN_SAFETY_CORE_H

#include <stdbool.h>
#include <stdint.h>

#define RB_BUMPER_MASK 0x3Fu
#define RB_WATCHDOG_MS 250u
#define RB_MOTION_LEASE_MS 250u
#define RB_LINEAR_LIMIT_MM_S 350
#define RB_ANGULAR_LIMIT_MRAD_S 1500
#define RB_LINEAR_ACCEL_MM_S2 500
#define RB_ANGULAR_ACCEL_MRAD_S2 2000
#define RB_HEAD_PAN_LIMIT_CDEG 6000
#define RB_HEAD_TILT_LIMIT_CDEG 2000

enum rb_safety_flag {
    RB_FLAG_ESTOP = 1u << 0,
    RB_FLAG_CHARGER = 1u << 1,
    RB_FLAG_LOW_BATTERY = 1u << 2,
    RB_FLAG_WATCHDOG = 1u << 3,
    RB_FLAG_MOTION_LEASE = 1u << 4,
    RB_FLAG_BUMPER = 1u << 5,
    RB_FLAG_WIRING = 1u << 6,
    RB_FLAG_MOTOR_ENABLE = 1u << 7,
};

enum rb_bumper_zone {
    RB_BUMPER_FRONT_LEFT = 1u << 0,
    RB_BUMPER_FRONT_RIGHT = 1u << 1,
    RB_BUMPER_REAR_LEFT = 1u << 2,
    RB_BUMPER_REAR_RIGHT = 1u << 3,
    RB_BUMPER_LEFT = 1u << 4,
    RB_BUMPER_RIGHT = 1u << 5,
};

typedef struct {
    uint32_t now_ms;
    uint32_t previous_tick_ms;
    uint32_t last_heartbeat_ms;
    uint32_t last_motion_ms;
    uint8_t released_mask;
    uint8_t bumper_latched_mask;
    uint8_t wiring_fault_mask;
    bool estop_released;
    bool estop_latched;
    bool charger_present;
    bool charger_latched;
    bool low_battery_latched;
    bool physical_reset_previous;
    uint16_t battery_mv;
    uint16_t low_battery_mv;
    uint16_t recovery_battery_mv;
    int16_t target_linear_mm_s;
    int16_t target_angular_mrad_s;
    int16_t applied_linear_mm_s;
    int16_t applied_angular_mrad_s;
    int16_t pan_cdeg;
    int16_t tilt_cdeg;
    uint16_t flags;
} rb_safety_state;

void rb_safety_init(rb_safety_state *state, uint32_t now_ms,
                    uint16_t low_battery_mv, uint16_t recovery_battery_mv);
void rb_safety_heartbeat(rb_safety_state *state, uint32_t now_ms);
void rb_safety_drive(rb_safety_state *state, uint32_t now_ms,
                     int16_t linear_mm_s, int16_t angular_mrad_s);
void rb_safety_stop(rb_safety_state *state);
void rb_safety_head(rb_safety_state *state, int16_t pan_cdeg, int16_t tilt_cdeg);
void rb_safety_clear_bumper(rb_safety_state *state, uint8_t requested_mask);
void rb_safety_inputs(rb_safety_state *state, uint32_t now_ms,
                      uint8_t released_mask, bool estop_released,
                      bool physical_reset_pressed, bool charger_present,
                      uint16_t battery_mv);
void rb_safety_tick(rb_safety_state *state, uint32_t now_ms);
bool rb_safety_motor_enable(const rb_safety_state *state);

#endif
