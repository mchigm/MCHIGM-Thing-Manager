# MCHIGM Thing Manager

A lightweight CLI application written in x86-64 assembly to help you manage your time, TODO lists, projects, and priorities.

## Features

- ✨ **Time Planner**: Create and manage time-based planning entries with descriptions and specific times
- 📅 **Timetable**: Organize your schedule with day-based time slots
- 📋 **Multiple Instances**: Create as many planners and timetables as needed (like GitHub issues)
- 💾 **Persistent Storage**: All data is saved to local files
- ⚡ **Lightweight**: Written in pure assembly with no dependencies
- 🔧 **Cross-platform Ready**: Designed with multi-platform support in mind

## Supported Platforms

- ✅ **Linux** (Debian, Ubuntu, MintOS) - x86-64 - **Fully Supported**
- 🔨 **macOS** - x86-64 - Requires modification (see docs)
- 🔨 **Windows** 10/11 - Requires separate implementation (see docs)

## Installation

### Prerequisites

**Linux/Debian/MintOS:**
```bash
sudo apt-get update
sudo apt-get install nasm build-essential
```

**macOS:**
```bash
brew install nasm
```

### Building from Source

```bash
# Clone the repository
git clone https://github.com/mchigm/MCHIGM-Thing-Manager.git
cd MCHIGM-Thing-Manager

# Build the application
make

# Run the application
./thing-manager
```

## Usage

### Main Menu

When you run the application, you'll see:

```
=== MCHIGM Thing Manager ===

Main Menu:
1. Create Time Planner
2. Create Timetable
3. List All Items
4. Exit
Select option:
```

### Creating a Time Planner

1. Select option `1` from the main menu
2. Enter a name for your planner (max 50 characters)
3. Enter a description (max 100 characters)
4. Enter a time in HH:MM format

**Example:**
```
Enter time planner name: Morning Workout
Enter description: 30-minute cardio session
Enter time: 07:00
```

### Creating a Timetable

1. Select option `2` from the main menu
2. Enter a name for your timetable (max 50 characters)
3. Enter the day of the week
4. Enter the time slot (e.g., 09:00-10:00)

**Example:**
```
Enter timetable name: Team Meeting
Enter day: Monday
Enter time slot: 10:00-11:00
```

### Listing All Items

Select option `3` to view all your time planners and timetables.

### Exiting

Select option `4` to exit the application.

## Data Storage

All data is stored in the `data/` directory:
- `data/planners.txt` - Time planner entries
- `data/timetables.txt` - Timetable entries

These files are created automatically when you save your first entry.

## Development

### Project Structure

```
MCHIGM-Thing-Manager/
├── src/
│   └── main.asm          # Main assembly source code
├── build/                # Build artifacts (generated)
├── data/                 # Data storage (generated)
├── docs/
│   └── ASSEMBLY_GUIDE.md # Detailed code documentation
├── Makefile              # Build configuration
├── README.md             # This file
└── LICENSE               # License information
```

### Make Commands

```bash
make           # Build the application
make clean     # Remove build artifacts and data
make run       # Build and run the application
make help      # Show help information
```

### Assembly Code

The application is written in NASM (Netwide Assembler) syntax for x86-64 architecture. See [docs/ASSEMBLY_GUIDE.md](docs/ASSEMBLY_GUIDE.md) for detailed code documentation including:

- System call reference
- Function documentation
- Memory layout
- File format specifications
- Debugging instructions
- Platform-specific notes

## Architecture

The application uses:
- **Linux x86-64 system calls** for I/O operations
- **Fixed-size buffers** for memory safety
- **Plain text files** for data persistence
- **Menu-driven interface** for user interaction

## Roadmap

Future features to be added as GitHub issues:

- [ ] Edit and delete functionality for planners/timetables
- [ ] Search and filter capabilities
- [ ] Priority management system
- [ ] Project tracking
- [ ] Color-coded output
- [ ] Input validation and error handling improvements
- [ ] macOS native support
- [ ] Windows native support
- [ ] Export/import functionality

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Technical Details

- **Language**: x86-64 Assembly (NASM syntax)
- **System Calls**: Linux x86-64 syscall interface
- **File I/O**: Direct syscalls (no libc)
- **Binary Size**: ~10KB (minimal footprint)
- **Dependencies**: None (standalone binary)

## License

See [LICENSE](LICENSE) file for details.

## Documentation

- [Assembly Code Guide](docs/ASSEMBLY_GUIDE.md) - Comprehensive documentation of the assembly implementation

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.

---

**Note**: This application is currently optimized for Linux x86-64 systems. Support for macOS and Windows requires platform-specific modifications as documented in the Assembly Guide.
