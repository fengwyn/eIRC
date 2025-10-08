#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

// Build for python modules
#include "Python.h"

// Structure to hold unpacked packet data
typedef struct {

    char *header;
    uint8_t *body;
    size_t body_len;
    char *date;

} PacketData;

// Builds packet from header and body strings
// Returns allocated byte array (caller must free)
// packet_len will contain the total packet length
uint8_t* build_packet(const char *header, const char *body, size_t *packet_len) {

    // Get lengths
    uint16_t header_len = strlen(header);
    uint16_t body_len = strlen(body);
    
    // Get current timestamp
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    char date_str[64];
    strftime(date_str, sizeof(date_str), "%B %d %Y %H:%M:%S", t);
    uint16_t date_len = strlen(date_str);
    
    // Calculate total packet size
    *packet_len = sizeof(uint16_t) + header_len +
                  sizeof(uint16_t) + body_len +
                  sizeof(uint16_t) + date_len;
    
    // Allocate packet buffer
    uint8_t *packet = (uint8_t*)malloc(*packet_len);
    if (!packet) return NULL;
    
    // Pack data (will be little-endian format)
    size_t offset = 0;
    
    // Pack header length and header
    memcpy(packet + offset, &header_len, sizeof(uint16_t));
    offset += sizeof(uint16_t);
    memcpy(packet + offset, header, header_len);
    offset += header_len;
    
    // Pack body length and body
    memcpy(packet + offset, &body_len, sizeof(uint16_t));
    offset += sizeof(uint16_t);
    memcpy(packet + offset, body, body_len);
    offset += body_len;
    
    // Pack date length and date
    memcpy(packet + offset, &date_len, sizeof(uint16_t));
    offset += sizeof(uint16_t);
    memcpy(packet + offset, date_str, date_len);
    
    return packet;
}

// Unpacks packet built by build_packet()
// Returns Packet structure (caller must free all the fields and structure)
PacketData* unpack_packet(const uint8_t *packet, size_t packet_len) {

    PacketData *data = (PacketData*)malloc(sizeof(PacketData));
    if (!data) return NULL;
    
    size_t offset = 0;
    
    // Unpack header
    uint16_t header_len;
    memcpy(&header_len, packet + offset, sizeof(uint16_t));
    offset += sizeof(uint16_t);
    
    data->header = (char*)malloc(header_len + 1);
    memcpy(data->header, packet + offset, header_len);
    data->header[header_len] = '\0';
    offset += header_len;
    
    // Unpack body
    uint16_t body_len;
    memcpy(&body_len, packet + offset, sizeof(uint16_t));
    offset += sizeof(uint16_t);
    
    data->body = (uint8_t*)malloc(body_len);
    data->body_len = body_len;
    memcpy(data->body, packet + offset, body_len);
    offset += body_len;
    
    // Unpack date
    uint16_t date_len;
    memcpy(&date_len, packet + offset, sizeof(uint16_t));
    offset += sizeof(uint16_t);
    
    data->date = (char*)malloc(date_len + 1);
    memcpy(data->date, packet + offset, date_len);
    data->date[date_len] = '\0';
    
    return data;
}

// Free Packet structure
void free_packet_data(PacketData *data) {

    if (data) {
        free(data->header);
        free(data->body);
        free(data->date);
        free(data);
    }
}



int main(int argc, char ** argv) {

    // Header and Body
    if (argc < 3) {
        perror("Invalid args: %d != 3\nUsage: <Header> <Body>");
        exit(argc);
    }

    char* header; char* body;
    strncpy(header, argv[1], size_t(char [128])); strncpy(body, argv[2], size_t(char [128]));

    if (header && body) {

    // Build a packet
    size_t packet_len;
    uint8_t *packet = build_packet(header, body, &packet_len);
    
    printf("Built packet of %zu bytes\n", packet_len);
    
    // Unpack the packet
    PacketData *data = unpack_packet(packet, packet_len);
    
    printf("Header: %s\n", data->header);
    printf("Body: %.*s\n", (int)data->body_len, data->body);
    printf("Date: %s\n", data->date);
    
    // Cleanup
    free_packet_data(data);
    free(packet);

    return EXIT_SUCCESS;
    }

    return EXIT_FAILURE;
}