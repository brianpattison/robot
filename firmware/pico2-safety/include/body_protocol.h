#ifndef ROVER_BEAN_BODY_PROTOCOL_H
#define ROVER_BEAN_BODY_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define RB_PROTOCOL_VERSION 1u
#define RB_PROTOCOL_MAX_PAYLOAD 64u

enum rb_message_type {
    RB_MSG_HEARTBEAT = 0x01,
    RB_MSG_DRIVE = 0x02,
    RB_MSG_STOP = 0x03,
    RB_MSG_CLEAR_BUMPER = 0x04,
    RB_MSG_STATUS_REQUEST = 0x05,
    RB_MSG_HEAD = 0x06,
    RB_MSG_ACK = 0x80,
    RB_MSG_STATUS = 0x81,
    RB_MSG_EVENT = 0x82,
};

typedef struct {
    uint8_t type;
    uint16_t sequence;
    uint16_t length;
    uint8_t payload[RB_PROTOCOL_MAX_PAYLOAD];
} rb_frame;

typedef struct {
    uint8_t buffer[2 + 6 + RB_PROTOCOL_MAX_PAYLOAD + 2];
    size_t used;
} rb_frame_parser;

uint16_t rb_crc16_ccitt(const uint8_t *data, size_t length);
void rb_parser_init(rb_frame_parser *parser);
bool rb_parser_push(rb_frame_parser *parser, uint8_t byte, rb_frame *frame);
size_t rb_frame_encode(const rb_frame *frame, uint8_t *output, size_t capacity);

#endif
