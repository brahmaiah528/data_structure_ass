# ====================================================================================================
# PROJECT: UNIVERSITY COURSE PREREQUISITE MANAGEMENT SYSTEM (C LANGUAGE)
# COURSE : CSA03 - Data Structures (Slot D)
# STUDENT: JAMPALA BRAHMAIAH (Register Number: 192472286)
# OUTCOME: CO5 - Robust Graph-Based Solutions & Topological Sort for Real-World Applications
# ====================================================================================================

CC ?= gcc
CFLAGS ?= -Wall -Wextra -pedantic -std=c99 -O2
TARGET = course_prerequisite_system
SRC = course_prerequisite_system.c

# Windows detection
ifeq ($(OS),Windows_NT)
    TARGET_BIN = $(TARGET).exe
    RM = del /Q /F
else
    TARGET_BIN = $(TARGET)
    RM = rm -f
endif

.PHONY: all run test clean help

all: $(TARGET_BIN)

$(TARGET_BIN): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET_BIN)
	@echo "Build successful: $(TARGET_BIN)"

run: $(TARGET_BIN)
	./$(TARGET_BIN)

test: $(TARGET_BIN)
	./$(TARGET_BIN) --all

clean:
	$(RM) $(TARGET) $(TARGET).exe *.o 2>/dev/null || true
	@echo "Clean completed."

help:
	@echo "Available targets:"
	@echo "  make         - Compile the C application"
	@echo "  make run     - Run the application in interactive CLI mode"
	@echo "  make test    - Run the automated 6-scenario test suite (--all mode)"
	@echo "  make clean   - Remove compiled binaries and objects"
