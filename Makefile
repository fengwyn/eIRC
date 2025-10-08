# Build C code utilities into Shared Objects

CC := gcc
CFLAGS := -Wall -Wextra -O2 -fPIC
LDFLAGS := -shared

SRC_DIR := src/utils
BUILD_DIR := build

SRC := $(SRC_DIR)/packet.c
TARGET := $(BUILD_DIR)/packet.so

all: $(TARGET)

$(TARGET): $(SRC)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) $(LDFLAGS) $< -o $@

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all clean
