# Edit Workflow Guide for MCHIGM Thing Manager

This guide documents the proper sequence and dependencies for editing files when implementing features or making updates to the application. Follow this workflow to ensure consistency and prevent breaking changes.

---

## Table of Contents

1. [Core Edit Sequence](#core-edit-sequence)
2. [Feature-Specific Workflows](#feature-specific-workflows)
3. [File Dependencies](#file-dependencies)
4. [Testing Checklist](#testing-checklist)
5. [Git Commit Procedure](#git-commit-procedure)

---

## Core Edit Sequence

**Always follow this order when making changes:**

### 1. Data Model Layer
**Files to edit (in order):**
- `src/database/models.py` — Add/modify SQLAlchemy models, enums, fields
- `tests/test_models.py` — Add tests for model changes

**Why:** Database schema defines the data structure for all layers above.

### 2. Core Logic & Services
**Files to edit (in order):**
- `src/settings_store.py` — Add new settings defaults (if applicable)
- `src/updater.py`, `src/scheduling.py`, `src/i18n.py` — Business logic modules
- `tests/test_settings_store.py`, `tests/test_updater.py`, etc. — Logic tests

**Why:** Business logic is independent of UI and must be testable in isolation.

### 3. UI Layer
**Files to edit (in order):**

#### A. Settings Window (if adding new settings)
- `src/ui/settings_window.py` — Add UI controls for new settings
  - Add field variables in `__init__` (e.g., `self._my_control = None`)
  - Build controls in appropriate `_build_*_tab()` method
  - Load values from settings in that tab builder
  - Save values in `_save_and_close()` method

#### B. Main Window (if adding new features/startup behavior)
- `src/ui/main_window.py` — Add top-level UI, navigation, startup hooks

#### C. Page-Specific Files (if adding feature to a page)
- `src/ui/pages/todos.py` — TODO/Kanban page
- `src/ui/pages/timetable.py` — Calendar page
- `src/ui/pages/memo.py` — AI Memo page
- `src/ui/pages/plan.py` — Roadmap/Plan page

**Why:** UI depends on settings, models, and business logic; must be built last.

### 4. Documentation & Tests
**Files to edit (in order):**
- `README.md` — Update feature list, settings documentation
- `CHANGELOG.md` — Add entry for the new feature (optional for internal features)
- `tests/test_*.py` (additional UI/integration tests) — Write comprehensive tests

**Why:** Documentation and tests validate that all pieces work together.

---

## Feature-Specific Workflows

### Adding a New Item Field (e.g., deadline, repeat_pattern)

**Edit sequence:**

1. **`src/database/models.py`**
   - Add `Column` to the `Item` class
   - If adding backward-compatibility migration logic, add helper function (e.g., `_ensure_item_schema_extensions()`)
   - Update `total_time_with_buffer()` or other model methods if affected

2. **`tests/test_models.py`**
   - Add test cases for the new field
   - Test with various values and edge cases

3. **`src/settings_store.py`** (if the field needs a default setting)
   - Add to `_DEFAULTS` dict

4. **`src/ui/pages/todos.py`** (if user needs to edit it)
   - Add `QDateTimeEdit`, `QCheckBox`, `QComboBox`, etc. to `ItemDetailsDialog` or `NewItemDialog`
   - Load current value from `item.<field>` in dialog `__init__`
   - Save value in `save_changes()` or `_create_item()`
   - Add static helper methods for type conversion (e.g., `_widget_datetime()`)

5. **`src/ui/pages/timetable.py`** or **`src/ui/pages/plan.py`**
   - If the field affects scheduling/display, add logic to filter or render items

6. **`tests/test_models.py`**
   - Add comprehensive tests

7. **`README.md`**
   - Document the new field in Features or Settings sections

---

### Adding a New Settings Control

**Edit sequence:**

1. **`src/settings_store.py`**
   - Add new key and default value to `_DEFAULTS` dict

2. **`src/ui/settings_window.py`**
   - Add field variable in `__init__()` (e.g., `self._my_control = None`)
   - Create UI control (combo, checkbox, text edit, etc.) in appropriate `_build_*_tab()` method
   - Set initial value from `self._settings.get("key", default)`
   - Add control to layout with label
   - In `_save_and_close()`, extract value from control and add to save dict

3. **`tests/test_settings_store.py`**
   - Add test to verify default is present
   - Test loading/saving the new setting

4. **`README.md`**
   - Document the setting in the Settings section

---

### Adding a Localized UI String

**Edit sequence:**

1. **`src/i18n.py`**
   - Add key-value pairs to both `"en"` and `"zh"` dictionaries in `_TRANSLATIONS`
   - Use consistent naming: `"feature.context.string_name"` (e.g., `"memo.install_cli"`)

2. **`src/ui/pages/*.py` or `src/ui/main_window.py` or `src/ui/settings_window.py`**
   - Replace hardcoded strings with `tr("key", "default_english_text")`
   - Always provide the default English text as fallback

3. **`README.md`**
   - Add localization notes if it's a user-visible feature

---

### Adding a New Page Feature or Refactoring a Page

**Edit sequence:**

1. **`src/ui/pages/<page>.py`**
   - Implement feature logic, UI controls, and event handlers
   - Add class variables, `_setup_ui()` layout, refresh/update methods

2. **`tests/test_*.py`** (if applicable)
   - Add tests for the new feature logic

3. **`README.md`**
   - Document the feature in the page description

---

### Adding a New Business Logic Module

**Edit sequence:**

1. **`src/<module>.py`** (e.g., `src/updater.py`, `src/scheduling.py`)
   - Implement pure logic functions/classes
   - No UI dependencies; use only standard library or data model imports
   - Add type hints and docstrings

2. **`tests/test_<module>.py`**
   - Write comprehensive unit tests
   - Test edge cases and error conditions

3. **`src/ui/main_window.py` or `src/ui/pages/*.py`**
   - Import and use the new module

4. **`README.md`**
   - Document the feature if user-facing

---

## File Dependencies

### Dependency Graph (edit in this order)

```
1. src/database/models.py
   ├─ defines Item, Scenario, Tag, Dependency classes

2. src/settings_store.py
   ├─ loads/saves user preferences
   └─ depends on: (none - uses stdlib)

3. src/version.py
   ├─ application version constant
   └─ depends on: (none - uses stdlib)

4. src/updater.py
   ├─ GitHub release checking
   └─ depends on: src/version.py, stdlib

5. src/scheduling.py
   ├─ recurring schedule logic
   └─ depends on: src/database/models.py, stdlib

6. src/i18n.py
   ├─ localization strings
   └─ depends on: src/settings_store.py

7. src/ui/main_window.py
   ├─ main application window
   └─ depends on: models, settings_store, updater, i18n, all pages

8. src/ui/settings_window.py
   ├─ settings dialog
   └─ depends on: settings_store, i18n, updater, mcp_client, calendar_sync

9. src/ui/pages/todos.py
   ├─ Kanban board page
   └─ depends on: models, settings_store, scheduling

10. src/ui/pages/timetable.py
    ├─ Calendar page
    └─ depends on: models, settings_store, scheduling, search_filters

11. src/ui/pages/memo.py
    ├─ AI Memo page
    └─ depends on: models, memo_agent, i18n

12. src/ui/pages/plan.py
    ├─ Roadmap/Gantt page
    └─ depends on: models, settings_store, scheduling

13. tests/test_*.py
    ├─ unit tests for all modules
    └─ depends on: corresponding module being tested

14. README.md, CHANGELOG.md
    ├─ documentation
    └─ depends on: all features implemented
```

### Key Rules

- **Never add UI imports to business logic modules** (updater, scheduling, i18n)
- **Always add settings defaults before using them in UI**
- **Database model changes must be backward-compatible** (use migration helpers)
- **All public functions need type hints and docstrings**

---

## Testing Checklist

After editing, **always run:**

```bash
# 1. Run all unit tests
pytest -q

# 2. Compile check modified Python files
python -m py_compile src/<module>.py src/ui/<page>.py

# 3. Check for import errors (optional but recommended)
python -c "from src.ui.main_window import MainWindow"

# 4. Manual UI test (if UI changes)
python main.py
```

### Test File Naming

- Test files must match: `tests/test_<module>.py`
- Test functions must start with `test_`
- Test classes must start with `Test`

Example:
```python
# tests/test_updater.py
class TestUpdater:
    def test_version_comparison(self):
        assert updater.is_newer_version("1.0.0", "1.1.0")
```

---

## Git Commit Procedure

### Before Committing

1. **Verify tests pass**
   ```bash
   pytest -q
   ```

2. **Check which files changed**
   ```bash
   git status
   ```

3. **Review diffs** (to catch unintended changes)
   ```bash
   git diff src/database/models.py
   ```

### Commit Message Format

Use this template:

```
<type>(<scope>): <subject>

<description>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `refactor` — Code reorganization (no behavior change)
- `test` — Adding/updating tests
- `docs` — Documentation updates
- `chore` — Maintenance, dependencies

**Scope (optional):** The module or component being changed (e.g., `updater`, `todos`, `settings`)

**Examples:**

```bash
git commit -m "feat(updater): Add GitHub-based auto-update system

- Implement updater.py with version checking
- Add update settings to General tab
- Wire startup auto-check behavior
- Add 157 unit tests

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

```bash
git commit -m "fix(todos): Correct link opening error handling

- Replace direct QLabel link activation with QDesktopServices
- Validate URLs before opening
- Add proper error messages

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Pushing Changes

```bash
git push origin <branch-name>
```

---

## Quick Reference: Common Edits

### Add a Boolean Setting
1. `src/settings_store.py` — add `"my_setting": False`
2. `src/ui/settings_window.py` — add `QCheckBox` and load/save logic
3. `tests/test_settings_store.py` — verify default
4. `README.md` — document

### Add a New Page
1. `src/ui/pages/<page>.py` — create `class <Page>Page(QWidget)`
2. `src/ui/main_window.py` — add to `_build_pages()`
3. Register in nav buttons
4. `tests/` — write tests if complex logic
5. `README.md` — add to Features

### Fix a Link/URL Issue
1. Replace `setOpenExternalLinks(True)` with manual `QDesktopServices.openUrl()`
2. Add validation (check if URL is valid)
3. Add error handling with QMessageBox
4. Write test in `tests/test_*.py`
5. Update relevant documentation

### Add Localization
1. `src/i18n.py` — add strings to both `"en"` and `"zh"` dicts
2. UI files — replace hardcoded strings with `tr("key", "default")`
3. Test by switching language in Settings
4. `README.md` — note localization support

---

## Troubleshooting Common Issues

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| Tests fail after model edit | DB schema mismatch | Check `_ensure_item_schema_extensions()` migration logic |
| Import error in UI file | Missing dependency | Verify import order: models → business logic → UI |
| Settings not persisting | Value not added to save dict | Check `_save_and_close()` includes new control |
| Localized string shows key instead of text | Missing i18n entry | Add to both `"en"` and `"zh"` dicts in `src/i18n.py` |
| Test coverage drops | New code not tested | Write test in `tests/test_<module>.py` before committing |

---

## Template: Adding a Complete Feature

Use this checklist when adding a new feature:

- [ ] 1. Model changes in `src/database/models.py` (if data storage needed)
- [ ] 2. Settings defaults in `src/settings_store.py` (if user configurable)
- [ ] 3. Business logic in `src/<module>.py` (if complex operations)
- [ ] 4. Localization strings in `src/i18n.py` (if user-facing)
- [ ] 5. Settings UI in `src/ui/settings_window.py` (if configurable)
- [ ] 6. Feature UI in `src/ui/pages/<page>.py` (if visible to user)
- [ ] 7. Main window hooks in `src/ui/main_window.py` (if startup/global behavior)
- [ ] 8. Unit tests in `tests/test_<module>.py` and `tests/test_settings_store.py`
- [ ] 9. Documentation in `README.md`
- [ ] 10. Run full test suite: `pytest -q`
- [ ] 11. Commit with proper message and Co-authored-by trailer

---

## Notes for Future AI Editors

- **Always run `pytest -q` before committing** — ensures no regressions
- **Follow the file dependency graph** — don't create circular imports
- **Type hints are required** — use `from __future__ import annotations` at top of files
- **Docstrings for public functions** — helps future maintainers
- **Test edge cases** — not just the happy path
- **Keep settings backward-compatible** — old users' settings.json must still load
- **Localization strings are not optional** — add both English and Chinese
- **Database migrations must be safe** — existing databases should not break

---

Generated: 2026-04-15
Last Updated: Auto-update system implementation (v1.0.0)
