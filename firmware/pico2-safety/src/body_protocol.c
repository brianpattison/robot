#include "body_protocol.h"

#include <string.h>

uint16_t rb_crc16_ccitt(const uint8_t *data, size_t length) {
    uint16_t crc = 0xFFFFu;
    for (size_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (unsigned bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
        }
    }
    return crc;
}
void rb_parser_init(rb_frame_parser *parser) {
    memset(parser, 0, sizeof(*parser));
}

static void consume(rb_frame_parser *parser, size_t count) {
    if (count >= parser->used) {
        parser->used = 0;
        return;
    }
    memmove(parser->buffer, parser->buffer + count, parser->used - count);
    parser->used -= count;
}

bool rb_parser_push(rb_frame_parser *parser, uint8_t byte, rb_frame *frame) {
    if (parser->used == sizeof(parser->buffer)) consume(parser, 1);
    parser->buffer[parser->used++] = byte;
    while (parser->used >= 2 && (parser->buffer[0] != 0xA5u || parser->buffer[1] != 0x5Au)) consume(parser, 1);
    if (parser->used < 8) return false;
    uint16_t length = (uint16_t)(parser->buffer[6] | ((uint16_t)parser->buffer[7] << 8));
    if (parser->buffer[2] != RB_PROTOCOL_VERSION || length > RB_PROTOCOL_MAX_PAYLOAD) {
        consume(parser, 1);
        return false;
    }
    size_t total = 2u + 6u + length + 2u;
    if (parser->used < total) return false;
    uint16_t expected = (uint16_t)(parser->buffer[8 + length] |
                                   ((uint16_t)parser->buffer[9 + length] << 8));
    if (rb_crc16_ccitt(parser->buffer + 2, 6u + length) != expected) {
        consume(parser, 1);
        return false;
    }
    frame->type = parser->buffer[3];
    frame->sequence = (uint16_t)(parser->buffer[4] | ((uint16_t)parser->buffer[5] << 8));
    frame->length = length;
    memcpy(frame->payload, parser->buffer + 8, length);
    consume(parser, total);
    return true;
}

size_t rb_frame_encode(const rb_frame *frame, uint8_t *output, size_t capacity) {
    if (frame->length > RB_PROTOCOL_MAX_PAYLOAD) return 0;
    size_t total = 2u + 6u + frame->length + 2u;
    if (capacity < total) return 0;
    output[0] = 0xA5u;
    output[1] = 0x5Au;
    output[2] = RB_PROTOCOL_VERSION;
    output[3] = frame->type;
    output[4] = (uint8_t)frame->sequence;
    output[5] = (uint8_t)(frame->sequence >> 8);
    output[6] = (uint8_t)frame->length;
    output[7] = (uint8_t)(frame->length >> 8);
    memcpy(output + 8, frame->payload, frame->length);
    uint16_t crc = rb_crc16_ccitt(output + 2, 6u + frame->length);
    output[8 + frame->length] = (uint8_t)crc;
    output[9 + frame->length] = (uint8_t)(crc >> 8);
    return total;
}
