# Makefile for MCHIGM Thing Manager
# Supports building for Linux (x86-64)

# Assembler and linker
NASM = nasm
LD = ld

# Flags
NASMFLAGS = -f elf64
LDFLAGS = 

# Directories
SRC_DIR = src
BUILD_DIR = build
DATA_DIR = data

# Files
SRC = $(SRC_DIR)/main.asm
OBJ = $(BUILD_DIR)/main.o
TARGET = thing-manager

.PHONY: all clean run install

all: $(TARGET)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(DATA_DIR):
	mkdir -p $(DATA_DIR)

$(TARGET): $(BUILD_DIR) $(DATA_DIR) $(OBJ)
	$(LD) $(LDFLAGS) -o $(TARGET) $(OBJ)

$(OBJ): $(SRC)
	$(NASM) $(NASMFLAGS) $(SRC) -o $(OBJ)

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(TARGET)
	rm -f $(DATA_DIR)/*.txt

run: $(TARGET)
	./$(TARGET)

install:
	@echo "Installing NASM assembler..."
	@command -v nasm >/dev/null 2>&1 || { \
		echo "NASM not found. Please install it:"; \
		echo "  Ubuntu/Debian: sudo apt-get install nasm"; \
		echo "  macOS: brew install nasm"; \
		echo "  Windows: Download from https://www.nasm.us/"; \
		exit 1; \
	}
	@echo "NASM is installed."

help:
	@echo "MCHIGM Thing Manager - Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  all      - Build the application (default)"
	@echo "  clean    - Remove build artifacts and data files"
	@echo "  run      - Build and run the application"
	@echo "  install  - Check if NASM is installed"
	@echo "  help     - Display this help message"
	@echo ""
	@echo "Platform support:"
	@echo "  Linux (x86-64)   - Fully supported"
	@echo "  macOS (x86-64)   - Requires modification for macOS syscalls"
	@echo "  Windows          - Requires separate implementation"
