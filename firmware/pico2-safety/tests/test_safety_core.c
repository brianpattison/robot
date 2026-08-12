#include "body_protocol.h"
#include "safety_core.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void release_and_reset(rb_safety_state *state, uint32_t now) {
    rb_safety_inputs(state, now, RB_BUMPER_MASK, true, false, false, 12800);
    rb_safety_inputs(state, now + 1, RB_BUMPER_MASK, true, true, false, 12800);
    rb_safety_tick(state, now + 1);
}

static void test_crc_and_frames(void) {
    assert(rb_crc16_ccitt((const uint8_t *)"123456789", 9) == 0x29B1u);
    rb_frame source = {.type = RB_MSG_DRIVE, .sequence = 42, .length = 4,
                       .payload = {0x85, 0xFF, 0xC8, 0x01}};
    uint8_t encoded[80];
    size_t length = rb_frame_encode(&source, encoded, sizeof(encoded));
    assert(length == 14);
    rb_frame_parser parser;
    rb_parser_init(&parser);
    rb_frame decoded;
    bool complete = false;
    for (size_t i = 0; i < length; ++i) complete = rb_parser_push(&parser, encoded[i], &decoded);
    assert(complete);
    assert(decoded.type == source.type && decoded.sequence == source.sequence);
    assert(decoded.length == source.length && memcmp(decoded.payload, source.payload, 4) == 0);
}

static void test_malformed_frame_rejection_and_resync(void) {
    rb_frame source = {.type = RB_MSG_HEARTBEAT, .sequence = 7, .length = 0};
    uint8_t encoded[80];
    size_t length = rb_frame_encode(&source, encoded, sizeof(encoded));
    assert(length == 10);
    rb_frame_parser parser;
    rb_parser_init(&parser);
    rb_frame decoded;
    const uint8_t noise[] = {0x00, 0xA5, 0x00, 0x5A, 0xFF};
    for (size_t i = 0; i < sizeof(noise); ++i) {
        assert(!rb_parser_push(&parser, noise[i], &decoded));
    }
    encoded[length - 1] ^= 0x55u;
    for (size_t i = 0; i < length; ++i) {
        assert(!rb_parser_push(&parser, encoded[i], &decoded));
    }
    encoded[length - 1] ^= 0x55u;
    bool complete = false;
    for (size_t i = 0; i < length; ++i) {
        complete = rb_parser_push(&parser, encoded[i], &decoded);
    }
    assert(complete);
    assert(decoded.type == RB_MSG_HEARTBEAT && decoded.sequence == 7);
}

static void test_physical_reset_and_watchdog(void) {
    rb_safety_state state;
    rb_safety_init(&state, 0, 11000, 11800);
    release_and_reset(&state, 10);
    assert(!state.estop_latched && !state.charger_latched);
    rb_safety_heartbeat(&state, 11);
    rb_safety_drive(&state, 11, 200, 0);
    rb_safety_tick(&state, 111);
    assert(state.applied_linear_mm_s > 0);
    rb_safety_tick(&state, 262);
    assert(state.applied_linear_mm_s == 0);
    assert(state.flags & RB_FLAG_WATCHDOG);
}

static void test_independent_motion_lease(void) {
    rb_safety_state state;
    rb_safety_init(&state, 0, 11000, 11800);
    release_and_reset(&state, 10);
    rb_safety_heartbeat(&state, 20);
    rb_safety_drive(&state, 20, 200, 0);
    rb_safety_tick(&state, 120);
    rb_safety_heartbeat(&state, 200);
    rb_safety_tick(&state, 271);
    assert(state.flags & RB_FLAG_MOTION_LEASE);
    assert(state.applied_linear_mm_s == 0);
    assert(!rb_safety_motor_enable(&state));
    assert(!(state.flags & RB_FLAG_WATCHDOG));
}

static void test_velocity_head_and_acceleration_clamps(void) {
    rb_safety_state state;
    rb_safety_init(&state, 0, 11000, 11800);
    release_and_reset(&state, 10);
    rb_safety_heartbeat(&state, 20);
    rb_safety_tick(&state, 20);
    rb_safety_drive(&state, 20, 1000, -3000);
    rb_safety_head(&state, 10000, -10000);
    rb_safety_tick(&state, 120);
    assert(state.target_linear_mm_s == 350);
    assert(state.target_angular_mrad_s == -1500);
    assert(state.applied_linear_mm_s == 50);
    assert(state.applied_angular_mrad_s == -200);
    assert(state.pan_cdeg == 6000 && state.tilt_cdeg == -2000);
}

static void test_bumper_open_clear_and_broken_wire(void) {
    rb_safety_state state;
    rb_safety_init(&state, 0, 11000, 11800);
    release_and_reset(&state, 10);
    rb_safety_heartbeat(&state, 20);
    rb_safety_inputs(&state, 30, RB_BUMPER_MASK & ~RB_BUMPER_FRONT_LEFT,
                     true, false, false, 12800);
    const int16_t commands[][2] = {
        {100, 0}, {-100, 0}, {0, 500}, {0, -500}, {100, 500}, {-100, -500},
    };
    uint32_t command_ms = 31;
    for (unsigned i = 0; i < sizeof(commands) / sizeof(commands[0]); ++i) {
        rb_safety_drive(&state, command_ms, commands[i][0], commands[i][1]);
        rb_safety_tick(&state, command_ms + 1);
        assert(state.target_linear_mm_s == 0);
        assert(state.target_angular_mrad_s == 0);
        assert(state.applied_linear_mm_s == 0);
        assert(state.applied_angular_mrad_s == 0);
        assert(!rb_safety_motor_enable(&state));
        command_ms += 10;
    }
    rb_safety_inputs(&state, 100, RB_BUMPER_MASK, true, false, false, 12800);
    rb_safety_clear_bumper(&state, RB_BUMPER_FRONT_LEFT);
    assert(state.bumper_latched_mask == 0);
    assert(state.wiring_fault_mask == 0);

    rb_safety_inputs(&state, 110, RB_BUMPER_MASK & ~RB_BUMPER_LEFT,
                     true, false, false, 12800);
    assert(state.wiring_fault_mask & RB_BUMPER_LEFT);
    rb_safety_clear_bumper(&state, RB_BUMPER_LEFT);
    assert(state.bumper_latched_mask & RB_BUMPER_LEFT);
    rb_safety_inputs(&state, 120, RB_BUMPER_MASK, true, false, false, 12800);
    rb_safety_clear_bumper(&state, RB_BUMPER_LEFT);
    assert(!(state.bumper_latched_mask & RB_BUMPER_LEFT));
    assert(!(state.wiring_fault_mask & RB_BUMPER_LEFT));
}

static void test_estop_charger_and_low_battery_latches(void) {
    rb_safety_state state;
    rb_safety_init(&state, 0, 11000, 11800);
    release_and_reset(&state, 10);
    rb_safety_inputs(&state, 20, RB_BUMPER_MASK, false, false, false, 12800);
    rb_safety_inputs(&state, 30, RB_BUMPER_MASK, true, false, false, 12800);
    rb_safety_tick(&state, 30);
    assert(state.estop_latched);
    rb_safety_inputs(&state, 40, RB_BUMPER_MASK, true, true, false, 12800);
    assert(!state.estop_latched);

    rb_safety_inputs(&state, 50, RB_BUMPER_MASK, true, false, true, 12800);
    rb_safety_inputs(&state, 60, RB_BUMPER_MASK, true, false, false, 12800);
    assert(state.charger_latched);
    rb_safety_inputs(&state, 70, RB_BUMPER_MASK, true, true, false, 12800);
    assert(!state.charger_latched);

    rb_safety_inputs(&state, 80, RB_BUMPER_MASK, true, false, false, 10900);
    rb_safety_inputs(&state, 90, RB_BUMPER_MASK, true, true, false, 11500);
    assert(state.low_battery_latched);
    rb_safety_inputs(&state, 100, RB_BUMPER_MASK, true, false, false, 12000);
    rb_safety_inputs(&state, 110, RB_BUMPER_MASK, true, true, false, 12000);
    assert(!state.low_battery_latched);
}

/* Stop-latency telemetry semantics under test: an event is recorded for every
   NEW onset of a stopping cause -- even while motor enable is already off for
   another reason, because commissioning triggers causes one at a time while
   parked -- but the deliberate boot-time latches never produce an event; a
   cause must first be seen inactive for one tick before its next onset
   counts. observed_ms is the update that first saw the input, enacted_ms is
   the tick that folded it into the motor-enable decision. */

static void start_running(rb_safety_state *state) {
    rb_safety_init(state, 0, 11000, 11800);
    release_and_reset(state, 10);
    rb_safety_heartbeat(state, 20);
    rb_safety_drive(state, 20, 200, 0);
    rb_safety_tick(state, 21);
    assert(rb_safety_motor_enable(state));
}

static void test_stop_event_bumper_edge_take_once(void) {
    rb_safety_state state;
    rb_stop_event event;
    start_running(&state);
    assert(!rb_safety_take_stop_event(&state, &event));
    rb_safety_inputs(&state, 50, RB_BUMPER_MASK & ~RB_BUMPER_FRONT_LEFT,
                     true, false, false, 12800);
    rb_safety_tick(&state, 52);
    assert(!rb_safety_motor_enable(&state));
    assert(rb_safety_take_stop_event(&state, &event));
    assert(event.cause_flags == (RB_FLAG_BUMPER | RB_FLAG_WIRING));
    assert(event.observed_ms == 50);
    assert(event.enacted_ms == 52);
    assert(event.dropped_events == 0);
    assert(!rb_safety_take_stop_event(&state, &event));
    /* Ticks while the same causes stay latched report nothing new. */
    rb_safety_tick(&state, 60);
    assert(!rb_safety_take_stop_event(&state, &event));
}

static void test_stop_event_latest_wins_and_dropped_counter(void) {
    rb_safety_state state;
    rb_stop_event event;
    start_running(&state);
    rb_safety_inputs(&state, 30, RB_BUMPER_MASK & ~RB_BUMPER_FRONT_LEFT,
                     true, false, false, 12800);
    rb_safety_tick(&state, 31);
    /* Continuity returns, the latch clears, and the wheels run again while
       the first event is still waiting to be taken. */
    rb_safety_inputs(&state, 40, RB_BUMPER_MASK, true, false, false, 12800);
    rb_safety_clear_bumper(&state, RB_BUMPER_FRONT_LEFT);
    rb_safety_heartbeat(&state, 40);
    rb_safety_drive(&state, 40, 200, 0);
    rb_safety_tick(&state, 41);
    rb_safety_inputs(&state, 60, RB_BUMPER_MASK, false, false, false, 12800);
    rb_safety_tick(&state, 62);
    assert(rb_safety_take_stop_event(&state, &event));
    assert(event.cause_flags == RB_FLAG_ESTOP);
    assert(event.observed_ms == 60);
    assert(event.enacted_ms == 62);
    assert(event.dropped_events == 1);
    assert(!rb_safety_take_stop_event(&state, &event));
}

static void test_stop_event_watchdog_attribution(void) {
    rb_safety_state state;
    rb_stop_event event;
    start_running(&state);
    rb_safety_drive(&state, 150, 200, 0);
    rb_safety_tick(&state, 151);
    assert(!rb_safety_take_stop_event(&state, &event));
    /* Heartbeat is stale, motion lease is still fresh: watchdog alone. */
    rb_safety_tick(&state, 280);
    assert(!rb_safety_motor_enable(&state));
    assert(rb_safety_take_stop_event(&state, &event));
    assert(event.cause_flags == RB_FLAG_WATCHDOG);
    assert(event.observed_ms == 280);
    assert(event.enacted_ms == 280);
    assert(event.dropped_events == 0);
}

static void test_stop_event_estop_attribution(void) {
    rb_safety_state state;
    rb_stop_event event;
    start_running(&state);
    rb_safety_inputs(&state, 50, RB_BUMPER_MASK, false, false, false, 12800);
    rb_safety_tick(&state, 53);
    assert(rb_safety_take_stop_event(&state, &event));
    assert(event.cause_flags == RB_FLAG_ESTOP);
    assert(event.observed_ms == 50);
    assert(event.enacted_ms == 53);
    assert(event.dropped_events == 0);
}

static void test_stop_event_no_spurious_boot_event(void) {
    rb_safety_state state;
    rb_stop_event event;
    rb_safety_init(&state, 0, 11000, 11800);
    /* Worst-case boot: every stopping input asserted on the first update. */
    rb_safety_inputs(&state, 5, 0, false, false, true, 10000);
    rb_safety_tick(&state, 6);
    assert(!rb_safety_motor_enable(&state));
    assert(!rb_safety_take_stop_event(&state, &event));
    rb_safety_tick(&state, 300);
    assert(!rb_safety_take_stop_event(&state, &event));
}

static void test_stop_event_onset_while_enable_already_off(void) {
    rb_safety_state state;
    rb_stop_event event;
    start_running(&state);
    rb_safety_inputs(&state, 30, RB_BUMPER_MASK & ~RB_BUMPER_FRONT_LEFT,
                     true, false, false, 12800);
    rb_safety_tick(&state, 32);
    assert(rb_safety_take_stop_event(&state, &event));
    assert(!rb_safety_motor_enable(&state));
    /* E-stop pressed while the bumper already holds enable off: still a new
       onset, attributed to the E-stop alone. */
    rb_safety_inputs(&state, 40, RB_BUMPER_MASK & ~RB_BUMPER_FRONT_LEFT,
                     false, false, false, 12800);
    rb_safety_tick(&state, 43);
    assert(rb_safety_take_stop_event(&state, &event));
    assert(event.cause_flags == RB_FLAG_ESTOP);
    assert(event.observed_ms == 40);
    assert(event.enacted_ms == 43);
    assert(event.dropped_events == 0);
}

int main(void) {
    test_crc_and_frames();
    test_malformed_frame_rejection_and_resync();
    test_physical_reset_and_watchdog();
    test_independent_motion_lease();
    test_velocity_head_and_acceleration_clamps();
    test_bumper_open_clear_and_broken_wire();
    test_estop_charger_and_low_battery_latches();
    test_stop_event_bumper_edge_take_once();
    test_stop_event_latest_wins_and_dropped_counter();
    test_stop_event_watchdog_attribution();
    test_stop_event_estop_attribution();
    test_stop_event_no_spurious_boot_event();
    test_stop_event_onset_while_enable_already_off();
    puts("SAFETY_CORE_TESTS_PASS");
    return 0;
}
