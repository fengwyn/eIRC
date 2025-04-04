CC=g++
CFLAGS = -Og
SOURCE_DIR=src
BUILD_DIR=build

$(BUILD_DIR)/main: $(SOURCE_DIR)/main.cpp
	$(CC) $(SOURCE_DIR)/main.cpp $(SOURCE_DIR)/interface.cpp $(CFLAGS) -o $(BUILD_DIR)/main
