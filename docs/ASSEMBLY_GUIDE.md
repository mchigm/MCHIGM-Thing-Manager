# MCHIGM Thing Manager - Assembly Code Documentation

## Overview
This document provides detailed documentation for the MCHIGM Thing Manager assembly code implementation.

## Architecture
The application is written in x86-64 assembly language using NASM (Netwide Assembler) syntax for Linux systems.

## File Structure
```
.
├── src/
│   └── main.asm          # Main application code
├── data/                 # Data storage directory
│   ├── planners.txt      # Time planner entries
│   └── timetables.txt    # Timetable entries
├── build/                # Build artifacts
├── Makefile              # Build configuration
└── docs/
    └── ASSEMBLY_GUIDE.md # This file
```

## System Calls Used

The application uses Linux x86-64 system calls:

| Syscall Number | Name      | Purpose                           |
|----------------|-----------|-----------------------------------|
| 0              | sys_read  | Read user input from stdin        |
| 1              | sys_write | Write output to stdout            |
| 2              | sys_open  | Open files for reading/writing    |
| 3              | sys_close | Close file descriptors            |
| 60             | sys_exit  | Exit the program                  |

## Register Usage Convention

The application follows the x86-64 System V ABI calling convention:

- **rax**: System call number and return values
- **rdi**: First argument (file descriptor, file path)
- **rsi**: Second argument (buffer pointer, flags)
- **rdx**: Third argument (buffer size, permissions)
- **r12**: Temporary storage for file descriptors
- **r13**: Temporary storage for byte counts

## Memory Sections

### .data Section
Contains initialized data including:
- Menu strings and prompts
- File paths
- Success and error messages
- Labels and formatting strings

### .bss Section
Contains uninitialized buffers for:
- User input (256 bytes)
- Name storage (51 bytes)
- Description storage (101 bytes)
- Time storage (11 bytes)
- Day storage (16 bytes)
- Time slot storage (21 bytes)
- File read buffer (4096 bytes)

### .text Section
Contains executable code including:
- Main entry point (_start)
- Menu display and navigation
- Input/output routines
- File operations
- Data persistence functions

## Core Functions

### _start
Entry point of the application. Displays welcome message and enters the main loop.

### main_loop
Main program loop that:
1. Displays the menu
2. Reads user choice
3. Dispatches to appropriate handler
4. Returns to menu or exits

### display_welcome
Displays the welcome banner using sys_write.

### display_menu
Displays the main menu options.

### read_choice
Reads a single character from stdin representing the user's menu choice.

### create_time_planner
Handles creation of a time planner entry:
1. Prompts for name (max 50 characters)
2. Prompts for description (max 100 characters)
3. Prompts for time (HH:MM format)
4. Saves to data/planners.txt
5. Displays success message

### create_timetable
Handles creation of a timetable entry:
1. Prompts for name (max 50 characters)
2. Prompts for day of week
3. Prompts for time slot (e.g., 09:00-10:00)
4. Saves to data/timetables.txt
5. Displays success message

### save_planner
Persists time planner data to file:
1. Opens data/planners.txt in append mode
2. Writes formatted planner entry
3. Closes file descriptor

File format:
```
Time Planner: [name][description][time]
```

### save_timetable
Persists timetable data to file:
1. Opens data/timetables.txt in append mode
2. Writes formatted timetable entry
3. Closes file descriptor

File format:
```
Timetable: [name][day][timeslot]
```

### list_items
Displays all stored items:
1. Opens and reads data/planners.txt
2. Displays planner entries
3. Opens and reads data/timetables.txt
4. Displays timetable entries

### display_file_contents
Helper function to read and display file contents.

### exit_program
Cleans up and exits the application:
1. Displays goodbye message
2. Calls sys_exit with code 0

## File Operations

### Opening Files
```asm
mov rax, 2                 ; sys_open
mov rdi, filename          ; Path to file
mov rsi, flags             ; Open flags
mov rdx, mode              ; File permissions (for creation)
syscall
```

Open flags used:
- `0` (O_RDONLY): Read-only mode
- `0x441` (O_WRONLY | O_CREAT | O_APPEND): Write, create if needed, append mode

### Writing to Files
```asm
mov rax, 1                 ; sys_write
mov rdi, fd                ; File descriptor
mov rsi, buffer            ; Data buffer
mov rdx, length            ; Number of bytes
syscall
```

### Reading from Files
```asm
mov rax, 0                 ; sys_read
mov rdi, fd                ; File descriptor
mov rsi, buffer            ; Destination buffer
mov rdx, max_bytes         ; Maximum bytes to read
syscall
```

### Closing Files
```asm
mov rax, 3                 ; sys_close
mov rdi, fd                ; File descriptor
syscall
```

## Data Persistence

The application stores data in plain text files in the `data/` directory:

- **planners.txt**: Contains time planner entries
- **timetables.txt**: Contains timetable entries

Both files use a simple format with one entry per "line" (though newlines are embedded in the data fields).

## Building the Application

### Prerequisites
- NASM assembler
- GNU ld linker
- Linux x86-64 system

### Build Commands
```bash
# Build the application
make

# Clean build artifacts
make clean

# Build and run
make run
```

## Platform-Specific Notes

### Linux (x86-64)
- Fully supported
- Uses standard Linux system calls
- Tested on Ubuntu, Debian, and compatible distributions

### macOS (x86-64)
- Requires modification of system call numbers
- macOS uses different syscall convention (syscall numbers offset by 0x2000000)
- File paths may need adjustment

### Windows
- Requires complete rewrite
- Windows uses different ABI and system calls
- Would need to use Windows API or create a separate implementation

## Extending the Application

### Adding New Menu Options
1. Add menu text to `.data` section
2. Add new choice comparison in `main_loop`
3. Implement handler function
4. Update documentation

### Adding New Data Fields
1. Add prompt strings to `.data` section
2. Add buffer in `.bss` section
3. Add read operation in create function
4. Update save function to persist new field

### Supporting Additional Platforms
1. Create platform-specific assembly file
2. Adjust system call numbers
3. Modify file paths if needed
4. Update Makefile with platform detection

## Error Handling

Current implementation includes basic error handling:
- File open failures are checked (cmp rax, 0; jl)
- Invalid menu choices display error message
- Non-existent files are handled gracefully in list operation

## Memory Safety

The application uses fixed-size buffers to prevent overflow:
- Input validation is implicit through buffer size limits
- No dynamic memory allocation (using .bss section)
- Stack is not used for data storage

## Performance Considerations

- Direct system calls minimize overhead
- No libc dependencies
- Small binary size (typically < 10KB)
- Fast startup time
- Minimal memory footprint

## Limitations

1. **Buffer Sizes**: Fixed maximum lengths for names, descriptions, etc.
2. **File Size**: Limited by 4KB read buffer in list operation
3. **No Delete/Edit**: Currently only supports create and list operations
4. **Single Platform**: Linux-only in current implementation
5. **No Input Validation**: Accepts any input within buffer limits
6. **No Search**: Cannot filter or search through items

## Future Enhancements

Potential improvements for future versions:
- Delete and edit functionality
- Search and filter capabilities
- Better input validation
- Color output support
- Priority management
- Project tracking
- Cross-platform support (macOS, Windows)
- Better file format (CSV, JSON)
- Multiple user support

## Debugging

To debug the assembly code:
```bash
# Build with debug symbols
nasm -f elf64 -g -F dwarf src/main.asm -o build/main.o
ld -o thing-manager build/main.o

# Run with GDB
gdb ./thing-manager
```

Useful GDB commands:
- `break _start` - Set breakpoint at entry
- `run` - Start execution
- `info registers` - View register values
- `x/20xb $rsi` - Examine memory at rsi
- `stepi` - Step one instruction
- `continue` - Continue execution

## References

- [NASM Documentation](https://www.nasm.us/doc/)
- [Linux System Call Table](https://blog.rchapman.org/posts/Linux_System_Call_Table_for_x86_64/)
- [x86-64 ABI Specification](https://refspecs.linuxbase.org/elf/x86_64-abi-0.99.pdf)
- [Intel 64 and IA-32 Architecture Manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
