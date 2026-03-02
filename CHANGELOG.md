# Changelog

All notable changes to MCHIGM Thing Manager are documented here.

## [v1.0.0] – First Release

### Added
- **Unified Item Model** – every entity (task, event, note, goal) is a single `Item` in SQLite, filtered by Type, Status, Time, Scenario and Tags.
- **TODOs page** – Kanban board (Backlog → To-Do → Doing → Done) with a time-tracker pop-up when items enter the *Doing* column.
- **Timetable page** – Day / Week / Month calendar with an unscheduled sidebar.
- **MEMO page** – AI Copilot chat/scratchpad powered by LiteLLM.
- **Plan page** – Gantt-style roadmap from Items, dependency lines, PDF export, and a weekly retrospective summary of recently completed items.
- **Omni-Search** – full-text search with `#tag`, `status:` and free-text filters across all pages.
- **Scenario filter** – context switcher that scopes all views to the active scenario.
- **Hotkeys** – Ctrl+1–4 for page navigation; Ctrl+Space for a quick-capture dialog that saves a Backlog note in the current scenario.
- **Settings** – persistent JSON settings store (`~/.mchigm_thing_manager/settings.json`).
- **Calendar sync stubs** – optional Google Calendar and Outlook sync (requires additional SDK packages).
- **Windows installer** – Inno Setup script produces `MCHIGM-Thing-Manager-Setup.exe` with shortcuts and optional data-cleanup on uninstall.
- **macOS installer** – `pkgbuild`/`productbuild` script produces a signed-ready `.pkg` with Welcome / ReadMe screens and automatic data-directory creation.
- **Setup wizard** – PyQt6 GUI for install, test, repair, settings management, and uninstall.
- **Uninstaller scripts** – `uninstall_windows.bat` and `uninstall_mac.sh` cleanly remove app data.
- **CI/CD** – GitHub Actions workflow builds Windows (.exe + Setup.exe) and macOS (.app.zip + .pkg) artifacts on version tags or manual dispatch, then publishes a GitHub Release automatically.
