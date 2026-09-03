@echo off
REM ====================================================================================================
REM PROJECT: UNIVERSITY COURSE PREREQUISITE MANAGEMENT SYSTEM (C LANGUAGE)
REM STUDENT: JAMPALA BRAHMAIAH (Register Number: 192472286)
REM COURSE : CSA03 - Data Structures (Slot D)
REM ====================================================================================================

echo ===============================================================================
echo Compiling University Course Prerequisite Management System (C Language)
echo ===============================================================================

REM 1. Try Windows GCC
where gcc >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Found Windows GCC. Compiling...
    gcc -Wall -Wextra -pedantic -std=c99 -O2 course_prerequisite_system.c -o course_prerequisite_system.exe
    if %ERRORLEVEL% equ 0 (
        echo [OK] Compilation successful: course_prerequisite_system.exe
        goto done
    )
)

REM 2. Try Windows Clang
where clang >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Found Windows Clang. Compiling...
    clang -Wall -Wextra -pedantic -std=c99 -O2 course_prerequisite_system.c -o course_prerequisite_system.exe
    if %ERRORLEVEL% equ 0 (
        echo [OK] Compilation successful: course_prerequisite_system.exe
        goto done
    )
)

REM 3. Try MSVC cl.exe
where cl >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Found MSVC cl.exe. Compiling...
    cl /W4 /O2 /Fe:course_prerequisite_system.exe course_prerequisite_system.c
    if %ERRORLEVEL% equ 0 (
        echo [OK] Compilation successful: course_prerequisite_system.exe
        goto done
    )
)

REM 4. Fallback to WSL GCC
where wsl >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Windows compiler not found in PATH. Using WSL GCC...
    wsl gcc -Wall -Wextra -pedantic -std=c99 -O2 course_prerequisite_system.c -o course_prerequisite_system
    if %ERRORLEVEL% equ 0 (
        echo [OK] Built Linux binary via WSL: ./course_prerequisite_system
        if "%1"=="--all" (
            wsl ./course_prerequisite_system --all
            exit /b 0
        )
        if "%1"=="--test" (
            wsl ./course_prerequisite_system --all
            exit /b 0
        )
        echo To run: wsl ./course_prerequisite_system
        exit /b 0
    )
)

echo [ERROR] No C compiler found! Please install GCC, Clang, or MSVC.
exit /b 1

:done
if "%1"=="--all" (
    course_prerequisite_system.exe --all
    exit /b 0
)
if "%1"=="--test" (
    course_prerequisite_system.exe --all
    exit /b 0
)
echo Run with: course_prerequisite_system.exe
echo Run test suite: course_prerequisite_system.exe --all
exit /b 0
