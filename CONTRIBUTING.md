# Contributing to MCHIGM Thing Manager

Thank you for considering contributing to MCHIGM Thing Manager! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- NASM assembler (2.14+)
- GNU ld linker
- make
- git
- Linux x86-64 system (for development)

### Getting Started
```bash
git clone https://github.com/mchigm/MCHIGM-Thing-Manager.git
cd MCHIGM-Thing-Manager
make
./thing-manager
```

## Project Structure

```
MCHIGM-Thing-Manager/
├── src/
│   └── main.asm          # Main assembly source
├── docs/
│   ├── ASSEMBLY_GUIDE.md # Code documentation
│   ├── QUICKSTART.md     # User quick start
│   └── EXAMPLES.md       # Data format examples
├── build/                # Generated build files
├── data/                 # User data storage
├── Makefile              # Build system
└── README.md             # Project overview
```

## How to Contribute

### Reporting Bugs

Before submitting a bug report:
1. Check existing issues to avoid duplicates
2. Test with the latest version
3. Gather relevant information (OS, architecture, error messages)

Create an issue with:
- Clear title describing the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, NASM version, etc.)

### Suggesting Features

Create an issue with:
- Clear description of the feature
- Use case explaining why it's useful
- Proposed implementation (if you have ideas)
- Compatibility considerations

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed
4. **Test your changes**
   ```bash
   make clean
   make
   # Test the application thoroughly
   ```
5. **Commit your changes**
   ```bash
   git commit -am "Add your meaningful commit message"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

## Coding Guidelines

### Assembly Code Style

1. **Comments**
   - Add section comments for major code blocks
   - Explain non-obvious assembly instructions
   - Document register usage in functions

2. **Naming Conventions**
   - Use descriptive labels: `create_time_planner` not `ctp`
   - Constants in UPPER_CASE: `MAX_NAME_LEN`
   - Labels use snake_case: `save_planner`

3. **Structure**
   - Keep functions focused and single-purpose
   - Limit function size (prefer ~50 lines)
   - Use consistent register conventions

4. **Formatting**
   - Indent with spaces (4 spaces)
   - Align comments at column 40
   - One instruction per line

### Example:
```asm
; Save time planner to file
; Input: name_buffer, desc_buffer, time_buffer populated
; Output: none
; Modifies: rax, rdi, rsi, rdx, r12
save_planner:
    mov rax, 2                 ; sys_open
    mov rdi, planners_file     ; File path
    mov rsi, 0x441             ; O_WRONLY | O_CREAT | O_APPEND
    mov rdx, 0644o             ; File permissions
    syscall
    
    ; Rest of implementation...
    ret
```

## Development Workflow

### Building
```bash
make              # Build the application
make clean        # Remove build artifacts
make run          # Build and run
```

### Testing
Currently, manual testing is required:
1. Build the application
2. Run through each menu option
3. Verify data persistence
4. Check edge cases

### Debugging
```bash
# Build with debug symbols
nasm -f elf64 -g -F dwarf src/main.asm -o build/main.o
ld -o thing-manager build/main.o

# Debug with GDB
gdb ./thing-manager
```

## Feature Areas

### High Priority
- [ ] Delete/edit functionality for existing items
- [ ] Search and filter capabilities
- [ ] Input validation improvements
- [ ] Better error handling

### Platform Support
- [ ] macOS x86-64 support (different syscalls)
- [ ] macOS ARM64 support
- [ ] Windows support (separate implementation)

### Enhancements
- [ ] Priority levels for tasks
- [ ] Project tracking
- [ ] Tags/categories
- [ ] Color output
- [ ] Export to CSV/JSON

### Infrastructure
- [ ] Automated testing
- [ ] CI/CD pipeline
- [ ] Binary releases
- [ ] Package manager integration (apt, brew, etc.)

## Platform-Specific Development

### macOS Support
macOS requires different system call numbers:
- Add 0x2000000 to syscall numbers
- Adjust file path conventions if needed
- Test on real macOS hardware

### Windows Support
Windows requires a completely different implementation:
- Use Windows API instead of syscalls
- Different ABI (different registers)
- MASM or NASM with Windows object format
- Create separate `src/main_windows.asm`

## Documentation

When adding features:
1. Update README.md with user-facing changes
2. Update ASSEMBLY_GUIDE.md with code documentation
3. Add examples to EXAMPLES.md if relevant
4. Update QUICKSTART.md for new workflows

## Questions?

- Create an issue for questions
- Tag with `question` label
- Check existing issues first

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Welcome newcomers
- Help each other learn

Thank you for contributing to MCHIGM Thing Manager!
