#include "safety_core.h"

#include <string.h>

static int16_t clamp_i16(int32_t value, int16_t limit) {
    if (value > limit) return limit;
    if (value < -limit) return (int16_t)-limit;
    return (int16_t)value;
}

static int16_t approach(int16_t current, int16_t target, uint32_t delta_ms, int32_t rate_per_s) {
    int32_t step = (rate_per_s * (int32_t)delta_ms) / 1000;
    if (step < 1 && delta_ms) step = 1;
    if (target > current) {
        int32_t next = (int32_t)current + step;
        return (int16_t)(next > target ? target : next);
    }
    if (target < current) {
        int32_t next = (int32_t)current - step;
        return (int16_t)(next < target ? target : next);
    }
    return current;
}

static bool escape_direction_ok(uint8_t open, int16_t linear, int16_t angular) {
    if ((open & (RB_BUMPER_FRONT_LEFT | RB_BUMPER_FRONT_RIGHT)) && linear > 0) return false;
    if ((open & (RB_BUMPER_REAR_LEFT | RB_BUMPER_REAR_RIGHT)) && linear < 0) return false;
    if ((open & (RB_BUMPER_FRONT_LEFT | RB_BUMPER_REAR_LEFT | RB_BUMPER_LEFT)) && angular > 0) return false;
    if ((open & (RB_BUMPER_FRONT_RIGHT | RB_BUMPER_REAR_RIGHT | RB_BUMPER_RIGHT)) && angular < 0) return false;
    return true;
}

static bool escape_window_open(const rb_safety_state *state, uint8_t open) {
    if (!open || (open & state->wiring_fault_mask)) return false;
    for (unsigned bit = 0; bit < 6; ++bit) {
        uint8_t mask = (uint8_t)(1u << bit);
        if ((open & mask) && (state->now_ms - state->open_since_ms[bit] > RB_ESCAPE_WINDOW_MS)) return false;
    }
    return true;
}

static bool escape_requested(const rb_safety_state *state, uint8_t open) {
    bool motion_requested = state->target_linear_mm_s != 0 || state->target_angular_mrad_s != 0;
    return motion_requested && escape_window_open(state, open) &&
        escape_direction_ok(open, state->target_linear_mm_s, state->target_angular_mrad_s);
}

void rb_safety_init(rb_safety_state *state, uint32_t now_ms,
                    uint16_t low_battery_mv, uint16_t recovery_battery_mv) {
    memset(state, 0, sizeof(*state));
    state->now_ms = now_ms;
    state->previous_tick_ms = now_ms;
    state->last_heartbeat_ms = now_ms - RB_WATCHDOG_MS - 1u;
    state->last_motion_ms = now_ms - RB_MOTION_LEASE_MS - 1u;
    state->low_battery_mv = low_battery_mv;
    state->recovery_battery_mv = recovery_battery_mv;
    state->estop_latched = true;
    state->charger_latched = true;
}

void rb_safety_heartbeat(rb_safety_state *state, uint32_t now_ms) {
    state->last_heartbeat_ms = now_ms;
}

void rb_safety_drive(rb_safety_state *state, uint32_t now_ms,
                     int16_t linear_mm_s, int16_t angular_mrad_s) {
    state->target_linear_mm_s = clamp_i16(linear_mm_s, RB_LINEAR_LIMIT_MM_S);
    state->target_angular_mrad_s = clamp_i16(angular_mrad_s, RB_ANGULAR_LIMIT_MRAD_S);
    state->last_motion_ms = now_ms;
}

void rb_safety_stop(rb_safety_state *state) {
    state->target_linear_mm_s = 0;
    state->target_angular_mrad_s = 0;
    state->applied_linear_mm_s = 0;
    state->applied_angular_mrad_s = 0;
}

void rb_safety_head(rb_safety_state *state, int16_t pan_cdeg, int16_t tilt_cdeg) {
    state->pan_cdeg = clamp_i16(pan_cdeg, RB_HEAD_PAN_LIMIT_CDEG);
    state->tilt_cdeg = clamp_i16(tilt_cdeg, RB_HEAD_TILT_LIMIT_CDEG);
}

void rb_safety_clear_bumper(rb_safety_state *state, uint8_t requested_mask) {
    uint8_t clearable = (uint8_t)(requested_mask & state->released_mask & ~state->wiring_fault_mask);
    state->bumper_latched_mask &= (uint8_t)~clearable;
}

void rb_safety_inputs(rb_safety_state *state, uint32_t now_ms,
                      uint8_t released_mask, bool estop_released,
                      bool physical_reset_pressed, bool charger_present,
                      uint16_t battery_mv) {
    state->now_ms = now_ms;
    released_mask &= RB_BUMPER_MASK;
    state->seen_released_mask |= released_mask;
    uint8_t open = (uint8_t)(~released_mask & RB_BUMPER_MASK);
    uint8_t newly_open = (uint8_t)(open & state->released_mask);
    for (unsigned bit = 0; bit < 6; ++bit) {
        uint8_t mask = (uint8_t)(1u << bit);
        if (newly_open & mask) state->open_since_ms[bit] = now_ms;
        if ((open & mask) && !(state->seen_released_mask & mask)) state->wiring_fault_mask |= mask;
        if ((open & mask) && state->open_since_ms[bit] &&
            now_ms - state->open_since_ms[bit] > RB_ESCAPE_WINDOW_MS) {
            state->wiring_fault_mask |= mask;
        }
        if (released_mask & mask) state->open_since_ms[bit] = 0;
    }
    state->bumper_latched_mask |= open;
    state->released_mask = released_mask;

    state->estop_released = estop_released;
    if (!estop_released) state->estop_latched = true;
    state->charger_present = charger_present;
    if (charger_present) state->charger_latched = true;
    state->battery_mv = battery_mv;
    if (battery_mv && battery_mv <= state->low_battery_mv) state->low_battery_latched = true;

    bool reset_edge = physical_reset_pressed && !state->physical_reset_previous;
    state->physical_reset_previous = physical_reset_pressed;
    if (reset_edge && estop_released && !charger_present &&
        battery_mv >= state->recovery_battery_mv && state->wiring_fault_mask == 0) {
        state->estop_latched = false;
        state->charger_latched = false;
        state->low_battery_latched = false;
        rb_safety_stop(state);
    }
}

void rb_safety_tick(rb_safety_state *state, uint32_t now_ms) {
    uint32_t delta_ms = now_ms - state->previous_tick_ms;
    state->previous_tick_ms = now_ms;
    state->now_ms = now_ms;
    bool watchdog_stale = now_ms - state->last_heartbeat_ms > RB_WATCHDOG_MS;
    bool lease_stale = now_ms - state->last_motion_ms > RB_MOTION_LEASE_MS;
    if (watchdog_stale || lease_stale) rb_safety_stop(state);

    uint8_t open = (uint8_t)(~state->released_mask & RB_BUMPER_MASK);
    bool escape = state->bumper_latched_mask && escape_requested(state, open);
    if (escape) {
        state->target_linear_mm_s = clamp_i16(state->target_linear_mm_s, RB_ESCAPE_LINEAR_LIMIT_MM_S);
        state->target_angular_mrad_s = clamp_i16(state->target_angular_mrad_s, RB_ESCAPE_ANGULAR_LIMIT_MRAD_S);
    } else if (state->bumper_latched_mask) rb_safety_stop(state);

    bool hard_fault = state->estop_latched || state->charger_latched || state->low_battery_latched ||
        state->wiring_fault_mask || watchdog_stale || lease_stale;
    if (hard_fault) rb_safety_stop(state);
    state->applied_linear_mm_s = approach(state->applied_linear_mm_s, state->target_linear_mm_s,
                                          delta_ms, RB_LINEAR_ACCEL_MM_S2);
    state->applied_angular_mrad_s = approach(state->applied_angular_mrad_s,
                                             state->target_angular_mrad_s,
                                             delta_ms, RB_ANGULAR_ACCEL_MRAD_S2);

    state->flags = 0;
    if (state->estop_latched) state->flags |= RB_FLAG_ESTOP;
    if (state->charger_latched || state->charger_present) state->flags |= RB_FLAG_CHARGER;
    if (state->low_battery_latched) state->flags |= RB_FLAG_LOW_BATTERY;
    if (watchdog_stale) state->flags |= RB_FLAG_WATCHDOG;
    if (lease_stale) state->flags |= RB_FLAG_MOTION_LEASE;
    if (state->bumper_latched_mask) state->flags |= RB_FLAG_BUMPER;
    if (state->wiring_fault_mask) state->flags |= RB_FLAG_WIRING;
    if (rb_safety_motor_enable(state)) state->flags |= RB_FLAG_MOTOR_ENABLE;
}

bool rb_safety_motor_enable(const rb_safety_state *state) {
    uint16_t blockers = RB_FLAG_ESTOP | RB_FLAG_CHARGER | RB_FLAG_LOW_BATTERY |
        RB_FLAG_WATCHDOG | RB_FLAG_MOTION_LEASE | RB_FLAG_WIRING;
    if (state->flags & blockers) return false;
    if (!(state->flags & RB_FLAG_BUMPER)) return true;
    uint8_t open = (uint8_t)(~state->released_mask & RB_BUMPER_MASK);
    return escape_requested(state, open);
}
