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

/* Every flag that forces motor enable off. */
#define RB_STOP_CAUSE_MASK \
    (RB_FLAG_ESTOP | RB_FLAG_CHARGER | RB_FLAG_LOW_BATTERY | RB_FLAG_WATCHDOG | \
     RB_FLAG_MOTION_LEASE | RB_FLAG_BUMPER | RB_FLAG_WIRING)

/* Stop-latency telemetry (read-only; it feeds nothing back into safety logic).
 *
 * Onset semantics: one event is recorded for every NEW onset of a stopping
 * cause (any flag in RB_STOP_CAUSE_MASK), regardless of whether motor enable
 * was already off for another reason -- commissioning triggers causes one at
 * a time while parked, and each trigger still deserves a number. A cause must
 * be observed inactive for at least one tick before its next onset counts;
 * rb_safety_init seeds every cause as already active, so the deliberate
 * boot-time latches (E-stop, charger, stale watchdog/lease, open bumper
 * loops) never produce a spurious event.
 *
 * observed_ms is the caller-provided now_ms of the update that first saw the
 * stopping input (rb_safety_inputs for E-stop, bumper, wiring, charger, and
 * low-battery edges; the expiring rb_safety_tick for watchdog and motion
 * lease). enacted_ms is the now_ms of the rb_safety_tick that folded the
 * cause into the motor-enable decision. Storage is a single latest-wins
 * slot: a newer event overwrites an untaken older one, and dropped_events
 * counts the events overwritten since the last take. */
typedef struct {
    uint16_t cause_flags;
    uint32_t observed_ms;
    uint32_t enacted_ms;
    uint16_t dropped_events;
} rb_stop_event;

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
    uint16_t stop_active_causes;
    uint16_t stop_pending_causes;
    uint32_t stop_pending_observed_ms;
    bool stop_event_pending;
    rb_stop_event stop_event;
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
/* Copies the most recent unreported stop event into *out and clears it.
   Returns false when no unreported event exists (take-semantics: a second
   call without a new onset returns false). */
bool rb_safety_take_stop_event(rb_safety_state *state, rb_stop_event *out);

#endif
