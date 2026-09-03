#!/usr/bin/env bash
# ====================================================================================================
# PROJECT: UNIVERSITY COURSE PREREQUISITE MANAGEMENT SYSTEM (C LANGUAGE)
# STUDENT: JAMPALA BRAHMAIAH (Register Number: 192472286)
# COURSE : CSA03 - Data Structures (Slot D)
# ====================================================================================================

set -e

CC=${CC:-gcc}
CFLAGS="-Wall -Wextra -pedantic -std=c99 -O2"
TARGET="course_prerequisite_system"
SRC="course_prerequisite_system.c"

echo "==============================================================================="
echo "Compiling University Course Prerequisite Management System with ${CC}"
echo "==============================================================================="

${CC} ${CFLAGS} ${SRC} -o ${TARGET}
echo "[OK] Build successful: ./${TARGET}"

if [ "$1" = "--all" ] || [ "$1" = "--test" ] || [ "$1" = "-a" ]; then
    echo ""
    echo ">>> Running automated test suite..."
    ./${TARGET} --all
fi
