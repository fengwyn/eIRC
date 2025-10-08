#ifndef PACKET_H
#define PACKET_H

    // Structure to hold unpacked packet data
    typedef struct {

        char *header;
        uint8_t *body;
        size_t body_len;
        char *date;

    } PacketData;

    extern uint8_t* build_packet(const char *header, const char *body, size_t *packet_len);
    extern PacketData* unpack_packet(const uint8_t *packet, size_t packet_len);

#endif