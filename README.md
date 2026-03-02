# MCHIGM Thing Manager

An AI-powered desktop time management app built with **PyQt6** and **SQLite**.

## Architecture

The app uses a **Unified Item Model**: every entity (task, event, note, goal) is
an `Item` in the database, filtered by Type, Status, Time, Scenario, and Tags.

### Four Pages
| # | Page | Description |
|---|------|-------------|
| 1 | **TODOs** | Kanban board (Backlog → To-Do → Doing → Done) + tracker pops up when items enter Doing |
| 2 | **Timetable** | Day / Week / Month calendar with unscheduled sidebar |
| 3 | **MEMO** | AI Copilot chat/scratchpad |
| 4 | **Plan** | Gantt roadmap & Weekly Retrospective |

## Phased Development

| Phase | Focus |
|-------|-------|
| 1 | Foundation — DB schema, GUI shell, Settings, Scenario filter |
| 2 | Core views (Kanban, Calendar) & Omni-Search |
| 3 | AI Brain — LLM integration & MEMO chat |
| 4 | MCP client, Google Calendar / Outlook sync |
| **5 （Current)** | Plan page (Gantt), Hotkeys, PDF export |

## Setup

### Prerequisites
- Python 3.11+
- A virtual environment (recommended)

### Install dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Run

```bash
python main.py
```

The SQLite database is created automatically at `~/.mchigm_thing_manager/things.db`.
Default scenarios, tags, and a handful of sample items are seeded on first launch so
the Kanban and Timetable views have data to display.

### AI (optional)
- Open **Settings → AI Agent** to set your model name (e.g., `gpt-4o-mini`, `claude-3-haiku`)
  and API key (stored locally at `~/.mchigm_thing_manager/settings.json`).
- Without a key, the MEMO page will still capture your text as a Backlog note.

### MCP Client (beta)
- Open **Settings → MCP Client** to point the app at an MCP server (e.g., Craft or Teams connectors).
- Install the official `mcp[cli]` package to enable live connections; the UI surfaces connection status.

## Building Executables

To compile the application into standalone executables for Windows or macOS, see [BUILD.md](BUILD.md) for detailed instructions.

**Quick start:**
- Windows: Run `build_windows.bat`
- macOS: Run `./build_mac.sh`

## Creating Installers

Professional installers are available for easier distribution:

**Windows Installer:**
- Build: `build_windows_installer.bat` (requires Inno Setup)
- Output: `installer_output/MCHIGM-Thing-Manager-Setup.exe`

**macOS Installer:**
- Build: `./build_macos_pkg.sh`
- Output: `installer_output/MCHIGM-Thing-Manager-1.0.0.pkg`

## Setup Wizard

A comprehensive setup wizard is available for managing installations:

```bash
python setup_wizard.py
```

Features:
- Install with configurable options
- Test installation integrity
- Repair corrupted installations
- Configure application settings
- Uninstall with optional data removal

## Uninstalling

To completely remove the application and all user data:
- Windows: Run `uninstall_windows.bat`
- macOS: Run `./uninstall_mac.sh`

See [BUILD.md](BUILD.md#uninstallation) for detailed uninstallation instructions.

## Project Structure

```
MCHIGM-Thing-Manager/
├── main.py                       # Entry point
├── requirements.txt
├── requirements-dev.txt          # Development dependencies (PyInstaller)
├── BUILD.md                      # Build instructions for executables
├── build_windows.bat             # Windows executable builder
├── build_mac.sh                  # macOS executable builder
├── build_windows_installer.bat   # Windows installer builder
├── build_macos_pkg.sh            # macOS pkg installer builder
├── installer_windows.iss         # Inno Setup script
├── setup_wizard.py               # Setup wizard (install/repair/test/uninstall)
├── uninstall_windows.bat         # Windows uninstaller
├── uninstall_mac.sh              # macOS uninstaller
├── MCHIGM-Thing-Manager.spec     # PyInstaller configuration
├── src/
│   ├── database/
│   │   └── models.py             # SQLAlchemy models: Item, Scenario, Tag, Dependency
│   └── ui/
│       ├── main_window.py        # Main window + navigation + scenario dropdown
│       ├── settings_window.py
│       └── pages/
│           ├── todos.py          # Kanban page
│           ├── timetable.py      # Calendar page
│           ├── memo.py           # AI MEMO page
│           └── plan.py           # Roadmap page
```
