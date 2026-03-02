# eIRC Build System

CXX      := g++
CC       := gcc

CXXFLAGS := -std=c++17 -Wall -Wextra -O2 -pthread
CFLAGS   := -Wall -Wextra -O2

BUILD_DIR  := build
UTILS_DIR  := src/utils
SERVER_DIR := src/server


# === Targets ===
NODE_BIN   := $(BUILD_DIR)/node
PACKET_SO  := $(BUILD_DIR)/packet.so
PACKET_BIN := $(BUILD_DIR)/packet_test


# === Object files for node server ===
NODE_OBJS := $(BUILD_DIR)/node.o          \
             $(BUILD_DIR)/node_commands.o  \
             $(BUILD_DIR)/tracker.o        \
             $(BUILD_DIR)/packet.o


# --- Default: build the node server ---
all: $(NODE_BIN)


# --- Node server binary ---
$(NODE_BIN): $(NODE_OBJS)
	$(CXX) $(CXXFLAGS) $^ -o $@


# --- C object (library mode, main() excluded) ---
$(BUILD_DIR)/packet.o: $(UTILS_DIR)/packet.c $(UTILS_DIR)/packet.h
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -DPACKET_LIB -c $< -o $@


# --- C++ objects ---
$(BUILD_DIR)/tracker.o: $(UTILS_DIR)/tracker.cpp $(UTILS_DIR)/tracker.h
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(BUILD_DIR)/node_commands.o: $(SERVER_DIR)/node_commands.cpp  \
                              $(SERVER_DIR)/node_commands.h     \
                              $(UTILS_DIR)/tracker.h            \
                              $(UTILS_DIR)/packet.h
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(BUILD_DIR)/node.o: $(SERVER_DIR)/node.cpp    \
                     $(SERVER_DIR)/node.h       \
                     $(SERVER_DIR)/node_commands.h \
                     $(UTILS_DIR)/tracker.h     \
                     $(UTILS_DIR)/packet.h
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@


# --- Standalone packet test binary (optional) ---
packet-test: $(PACKET_BIN)

$(PACKET_BIN): $(UTILS_DIR)/packet.c $(UTILS_DIR)/packet.h
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) $< -o $@


# --- Shared object for Python ctypes (optional) ---
packet-so: $(PACKET_SO)

$(PACKET_SO): $(UTILS_DIR)/packet.c $(UTILS_DIR)/packet.h
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -fPIC -shared -DPACKET_LIB $< -o $@


clean:
	rm -rf $(BUILD_DIR)

.PHONY: all clean packet-test packet-so
