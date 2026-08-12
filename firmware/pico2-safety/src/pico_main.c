#include "body_protocol.h"
#include "safety_core.h"

#include "hardware/adc.h"
#include "hardware/uart.h"
#include "pico/stdlib.h"

#ifndef RB_HARDWARE_RELEASE
#define RB_HARDWARE_RELEASE 0
#endif

#define RB_UART uart0
#define RB_UART_TX_PIN 0
#define RB_UART_RX_PIN 1
#define RB_RESET_PIN 9
#define RB_ESTOP_SENSE_PIN 8
#define RB_CHARGER_SENSE_PIN 10
#define RB_RELAY_ENABLE_PIN 11

static const uint8_t bumper_pins[6] = {2, 3, 4, 5, 6, 7};
static rb_safety_state safety;
static rb_frame_parser parser;
static uint16_t tx_sequence;

static uint16_t read_u16(const uint8_t *data) {
    return (uint16_t)(data[0] | ((uint16_t)data[1] << 8));
}

static int16_t read_i16(const uint8_t *data) {
    return (int16_t)read_u16(data);
}

static void write_u16(uint8_t *data, uint16_t value) {
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
}

static void write_u32(uint8_t *data, uint32_t value) {
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
    data[2] = (uint8_t)(value >> 16);
    data[3] = (uint8_t)(value >> 24);
}

static void send_frame(const rb_frame *frame) {
    uint8_t encoded[80];
    size_t length = rb_frame_encode(frame, encoded, sizeof(encoded));
    if (length) uart_write_blocking(RB_UART, encoded, length);
}

static void send_ack(uint8_t command, uint8_t result) {
    rb_frame frame = {.type = RB_MSG_ACK, .sequence = ++tx_sequence, .length = 2,
                      .payload = {command, result}};
    send_frame(&frame);
}

static void send_status(void) {
    rb_frame frame = {.type = RB_MSG_STATUS, .sequence = ++tx_sequence, .length = 18};
    write_u32(frame.payload + 0, safety.now_ms);
    uint16_t reported_flags = safety.flags;
    if (!RB_HARDWARE_RELEASE) reported_flags &= (uint16_t)~RB_FLAG_MOTOR_ENABLE;
    write_u16(frame.payload + 4, reported_flags);
    frame.payload[6] = safety.released_mask;
    frame.payload[7] = safety.bumper_latched_mask;
    write_u16(frame.payload + 8, safety.battery_mv);
    write_u16(frame.payload + 10, (uint16_t)safety.applied_linear_mm_s);
    write_u16(frame.payload + 12, (uint16_t)safety.applied_angular_mrad_s);
    write_u16(frame.payload + 14, (uint16_t)safety.pan_cdeg);
    write_u16(frame.payload + 16, (uint16_t)safety.tilt_cdeg);
    send_frame(&frame);
}

static void send_stop_event(const rb_stop_event *event) {
    /* Telemetry only: the safety core self-reports the tick that observed a
       stopping input and the tick that dropped motor enable. Emitting (or
       not emitting) this frame never changes any output decision. Payload,
       little-endian: u8 event_type=0x01, u16 cause_flags, u32 observed_ms,
       u32 enacted_ms, u16 dropped_events. */
    rb_frame frame = {.type = RB_MSG_EVENT, .sequence = ++tx_sequence, .length = 13,
                      .payload = {RB_EVENT_STOP_LATENCY}};
    write_u16(frame.payload + 1, event->cause_flags);
    write_u32(frame.payload + 3, event->observed_ms);
    write_u32(frame.payload + 7, event->enacted_ms);
    write_u16(frame.payload + 11, event->dropped_events);
    send_frame(&frame);
}

static void handle_frame(const rb_frame *frame, uint32_t now_ms) {
    switch (frame->type) {
        case RB_MSG_HEARTBEAT:
            if (frame->length) { send_ack(frame->type, 1); break; }
            rb_safety_heartbeat(&safety, now_ms);
            break;
        case RB_MSG_DRIVE:
            if (frame->length != 4) { send_ack(frame->type, 1); break; }
            rb_safety_drive(&safety, now_ms, read_i16(frame->payload), read_i16(frame->payload + 2));
            send_ack(frame->type, 0);
            break;
        case RB_MSG_STOP:
            if (frame->length) { send_ack(frame->type, 1); break; }
            rb_safety_stop(&safety);
            send_ack(frame->type, 0);
            break;
        case RB_MSG_CLEAR_BUMPER:
            if (frame->length != 1) { send_ack(frame->type, 1); break; }
            rb_safety_clear_bumper(&safety, frame->payload[0]);
            send_ack(frame->type, 0);
            break;
        case RB_MSG_STATUS_REQUEST:
            if (frame->length) { send_ack(frame->type, 1); break; }
            send_status();
            break;
        case RB_MSG_HEAD:
            if (frame->length != 4) { send_ack(frame->type, 1); break; }
            rb_safety_head(&safety, read_i16(frame->payload), read_i16(frame->payload + 2));
            send_ack(frame->type, 0);
            break;
        default:
            send_ack(frame->type, 2);
            break;
    }
}

static uint8_t read_released_bumpers(void) {
    uint8_t released = 0;
    for (unsigned index = 0; index < 6; ++index) {
        if (!gpio_get(bumper_pins[index])) released |= (uint8_t)(1u << index);
    }
    return released;
}

static void apply_outputs(void) {
    /* Production motor PWM/mixing is intentionally not released here. Even if
       someone flips this compile definition, motor enable remains low until a
       reviewed output driver exists. */
    bool enable = false;
    if (RB_HARDWARE_RELEASE) {
        enable = false;
    }
    gpio_put(RB_RELAY_ENABLE_PIN, enable && rb_safety_motor_enable(&safety));
}

int main(void) {
    uart_init(RB_UART, 115200);
    gpio_set_function(RB_UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(RB_UART_RX_PIN, GPIO_FUNC_UART);
    for (unsigned index = 0; index < 6; ++index) {
        gpio_init(bumper_pins[index]);
        gpio_set_dir(bumper_pins[index], GPIO_IN);
        gpio_pull_up(bumper_pins[index]);
    }
    for (uint8_t pin = RB_ESTOP_SENSE_PIN; pin <= RB_CHARGER_SENSE_PIN; ++pin) {
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_IN);
        gpio_pull_up(pin);
    }
    gpio_init(RB_RELAY_ENABLE_PIN);
    gpio_set_dir(RB_RELAY_ENABLE_PIN, GPIO_OUT);
    gpio_put(RB_RELAY_ENABLE_PIN, false);
    adc_init();
    rb_parser_init(&parser);
    rb_safety_init(&safety, to_ms_since_boot(get_absolute_time()), 11000, 11800);

    uint32_t last_status_ms = 0;
    while (true) {
        uint32_t now_ms = to_ms_since_boot(get_absolute_time());
        while (uart_is_readable(RB_UART)) {
            rb_frame frame;
            if (rb_parser_push(&parser, uart_getc(RB_UART), &frame)) handle_frame(&frame, now_ms);
        }
        rb_safety_inputs(&safety, now_ms, read_released_bumpers(),
                         !gpio_get(RB_ESTOP_SENSE_PIN), !gpio_get(RB_RESET_PIN),
                         gpio_get(RB_CHARGER_SENSE_PIN), 0);
        rb_safety_tick(&safety, now_ms);
        apply_outputs();
        rb_stop_event stop_event;
        if (rb_safety_take_stop_event(&safety, &stop_event)) send_stop_event(&stop_event);
        if (now_ms - last_status_ms >= 100) {
            send_status();
            last_status_ms = now_ms;
        }
        sleep_ms(1);
    }
}
