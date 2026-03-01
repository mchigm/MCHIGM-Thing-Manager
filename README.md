# MCHIGM Thing Manager

An AI-powered desktop time management app built with **PyQt6** and **SQLite**.

## Architecture

The app uses a **Unified Item Model**: every entity (task, event, note, goal) is
an `Item` in the database, filtered by Type, Status, Time, Scenario, and Tags.

### Four Pages
| # | Page | Description |
|---|------|-------------|
| 1 | **TODOs** | Kanban board (Backlog → To-Do → Doing → Done) |
| 2 | **Timetable** | Day / Week / Month calendar with unscheduled sidebar |
| 3 | **MEMO** | AI Copilot chat/scratchpad |
| 4 | **Plan** | Gantt roadmap & Weekly Retrospective |

## Phased Development

| Phase | Focus |
|-------|-------|
| **1 (current)** | Foundation — DB schema, GUI shell, Settings, Scenario filter |
| 2 | Core views (Kanban, Calendar) & Omni-Search |
| 3 | AI Brain — LLM integration & MEMO chat |
| 4 | MCP client, Google Calendar / Outlook sync |
| 5 | Plan page (Gantt), Hotkeys, PDF export |

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

## Project Structure

```
MCHIGM-Thing-Manager/
├── main.py                   # Entry point
├── requirements.txt
├── src/
│   ├── database/
│   │   └── models.py         # SQLAlchemy models: Item, Scenario, Tag, Dependency
│   └── ui/
│       ├── main_window.py    # Main window + navigation + scenario dropdown
│       ├── settings_window.py
│       └── pages/
│           ├── todos.py      # Kanban page
│           ├── timetable.py  # Calendar page
│           ├── memo.py       # AI MEMO page
│           └── plan.py       # Roadmap page
```
