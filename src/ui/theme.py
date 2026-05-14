"""
Central design tokens & shared stylesheets for MCHIGM Thing Manager.

This module is the single source of truth for colors, spacing, radii,
typography and reusable QSS snippets. UI files should pull values from
here instead of hard-coding hex strings inline. The goal is a calmer,
more consistent dark UI inspired by Linear/Raycast: a near-black
background, a single restrained accent color, and tighter visual rhythm.

If you need a one-off color, add it here first and reference it by name.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Color tokens
# ---------------------------------------------------------------------------
class Color:
    # Surfaces (lowest to highest elevation)
    BG = "#0f1117"             # app background — deep, slightly blue near-black
    SURFACE = "#161922"        # cards, panels, sidebar
    SURFACE_ALT = "#1c2030"    # input fields, secondary surfaces
    SURFACE_HOVER = "#232838"  # hover/focus background
    SURFACE_ACTIVE = "#2a3047" # active nav, pressed buttons

    # Borders / dividers
    BORDER = "#262b3a"
    BORDER_STRONG = "#323848"
    DIVIDER = "#1f2330"

    # Text
    TEXT = "#e6e8ef"           # primary text
    TEXT_MUTED = "#9aa0b8"     # secondary labels
    TEXT_FAINT = "#6b7290"     # placeholders, hints
    TEXT_INVERSE = "#0f1117"

    # Single accent (used sparingly — focus rings, active states, primary buttons)
    ACCENT = "#7c8cff"
    ACCENT_HOVER = "#8c9bff"
    ACCENT_SUBTLE = "#2a2f55"  # tinted background for selected/active

    # Semantic colors (status, deadlines, levels)
    SUCCESS = "#5fd49a"
    WARNING = "#e9b66b"
    DANGER = "#ee6b6e"
    INFO = "#6cc1ff"

    # Kanban column accents (softened from the originals)
    COL_BACKLOG = "#4a5063"
    COL_TODO = "#4d6f96"
    COL_DOING = "#7a5fb8"
    COL_DONE = "#4ea776"

    # Scenario seed colors (used when seeding default scenarios)
    SCENARIO_SCHOOL = "#7c8cff"
    SCENARIO_WORK = "#e9b66b"
    SCENARIO_PERSONAL = "#5fd49a"


# ---------------------------------------------------------------------------
# Spacing & sizing
# ---------------------------------------------------------------------------
class Size:
    # 4px base scale
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32

    # Component sizing
    TOP_BAR_HEIGHT = 44
    NAV_WIDTH = 168
    FILTER_BAR_HEIGHT = 52
    INPUT_HEIGHT = 28

    # Radii
    RADIUS_SM = 4
    RADIUS_MD = 6
    RADIUS_LG = 10


class Font:
    SIZE_XS = "11px"
    SIZE_SM = "12px"
    SIZE_MD = "13px"
    SIZE_LG = "15px"
    SIZE_XL = "18px"
    WEIGHT_NORMAL = "400"
    WEIGHT_MEDIUM = "500"
    WEIGHT_SEMIBOLD = "600"


# ---------------------------------------------------------------------------
# App-wide stylesheet (set on the QApplication)
# ---------------------------------------------------------------------------
APP_STYLE = f"""
* {{
    outline: none;
}}

QMainWindow, QWidget {{
    background-color: {Color.BG};
    color: {Color.TEXT};
    font-size: {Font.SIZE_MD};
}}

QLabel {{
    background: transparent;
    color: {Color.TEXT};
}}

/* Scrollbars — slim, subtle */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {Color.BORDER_STRONG};
    min-height: 24px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Color.TEXT_FAINT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: transparent;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {Color.BORDER_STRONG};
    min-width: 24px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {Color.TEXT_FAINT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: transparent;
}}

/* Tooltips */
QToolTip {{
    background-color: {Color.SURFACE_ACTIVE};
    color: {Color.TEXT};
    border: 1px solid {Color.BORDER_STRONG};
    border-radius: {Size.RADIUS_SM}px;
    padding: 4px 8px;
}}

/* Generic inputs (line edit, text edit, spin, date) */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateTimeEdit, QDateEdit {{
    background-color: {Color.SURFACE_ALT};
    color: {Color.TEXT};
    border: 1px solid {Color.BORDER};
    border-radius: {Size.RADIUS_SM}px;
    padding: 5px 8px;
    selection-background-color: {Color.ACCENT_SUBTLE};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus, QDateEdit:focus {{
    border: 1px solid {Color.ACCENT};
}}
QLineEdit::placeholder, QTextEdit::placeholder {{
    color: {Color.TEXT_FAINT};
}}

/* Combo boxes */
QComboBox {{
    background-color: {Color.SURFACE_ALT};
    color: {Color.TEXT};
    border: 1px solid {Color.BORDER};
    border-radius: {Size.RADIUS_SM}px;
    padding: 4px 10px;
    min-height: 20px;
}}
QComboBox:hover {{
    border: 1px solid {Color.BORDER_STRONG};
}}
QComboBox:focus {{
    border: 1px solid {Color.ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 18px;
}}
QComboBox QAbstractItemView {{
    background-color: {Color.SURFACE};
    color: {Color.TEXT};
    border: 1px solid {Color.BORDER_STRONG};
    border-radius: {Size.RADIUS_SM}px;
    selection-background-color: {Color.ACCENT_SUBTLE};
    selection-color: {Color.TEXT};
    padding: 4px;
    outline: none;
}}

/* Buttons (default) */
QPushButton {{
    background-color: {Color.SURFACE_ALT};
    color: {Color.TEXT};
    border: 1px solid {Color.BORDER};
    border-radius: {Size.RADIUS_SM}px;
    padding: 5px 12px;
    font-size: {Font.SIZE_SM};
    font-weight: {Font.WEIGHT_MEDIUM};
}}
QPushButton:hover {{
    background-color: {Color.SURFACE_HOVER};
    border-color: {Color.BORDER_STRONG};
}}
QPushButton:pressed {{
    background-color: {Color.SURFACE_ACTIVE};
}}
QPushButton:disabled {{
    color: {Color.TEXT_FAINT};
    background-color: {Color.SURFACE};
}}
QPushButton:checked {{
    background-color: {Color.ACCENT_SUBTLE};
    border-color: {Color.ACCENT};
    color: {Color.TEXT};
}}

/* Checkboxes */
QCheckBox {{
    color: {Color.TEXT};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid {Color.BORDER_STRONG};
    background: {Color.SURFACE_ALT};
}}
QCheckBox::indicator:hover {{
    border-color: {Color.ACCENT};
}}
QCheckBox::indicator:checked {{
    background: {Color.ACCENT};
    border-color: {Color.ACCENT};
    image: none;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {Color.BORDER};
    border-radius: {Size.RADIUS_MD}px;
    background-color: {Color.SURFACE};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {Color.TEXT_MUTED};
    padding: 8px 14px;
    border: none;
    margin-right: 2px;
    font-weight: {Font.WEIGHT_MEDIUM};
}}
QTabBar::tab:selected {{
    color: {Color.TEXT};
    border-bottom: 2px solid {Color.ACCENT};
}}
QTabBar::tab:hover:!selected {{
    color: {Color.TEXT};
}}

/* Group box */
QGroupBox {{
    border: 1px solid {Color.BORDER};
    border-radius: {Size.RADIUS_MD}px;
    margin-top: 12px;
    padding-top: 8px;
    color: {Color.TEXT};
    font-weight: {Font.WEIGHT_SEMIBOLD};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {Color.TEXT_MUTED};
}}

/* Menus */
QMenu {{
    background: {Color.SURFACE};
    color: {Color.TEXT};
    border: 1px solid {Color.BORDER_STRONG};
    border-radius: {Size.RADIUS_MD}px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 14px;
    border-radius: {Size.RADIUS_SM}px;
}}
QMenu::item:selected {{
    background: {Color.ACCENT_SUBTLE};
}}

/* Dialogs */
QDialog {{
    background-color: {Color.BG};
}}

/* Calendar widget (used on Timetable) */
QCalendarWidget QWidget {{ alternate-background-color: {Color.SURFACE}; }}
QCalendarWidget QAbstractItemView:enabled {{
    color: {Color.TEXT};
    background: {Color.SURFACE};
    selection-background-color: {Color.ACCENT_SUBTLE};
    selection-color: {Color.TEXT};
}}
QCalendarWidget QToolButton {{
    color: {Color.TEXT};
    background: transparent;
    border: none;
    padding: 6px;
}}
QCalendarWidget QToolButton:hover {{
    background: {Color.SURFACE_HOVER};
    border-radius: 4px;
}}
QCalendarWidget QMenu {{ background: {Color.SURFACE}; }}
QCalendarWidget QSpinBox {{
    background: {Color.SURFACE_ALT};
}}
"""


# ---------------------------------------------------------------------------
# Per-component QSS snippets
# ---------------------------------------------------------------------------
TOP_BAR_QSS = f"""
QWidget#TopBar {{
    background-color: {Color.SURFACE};
    border-bottom: 1px solid {Color.BORDER};
}}
QLabel#AppName {{
    color: {Color.TEXT};
    font-size: {Font.SIZE_MD};
    font-weight: {Font.WEIGHT_SEMIBOLD};
    letter-spacing: 0.2px;
}}
QLabel#TopBarLabel {{
    color: {Color.TEXT_MUTED};
    font-size: {Font.SIZE_SM};
}}
"""


NAV_BAR_QSS = f"""
QWidget#NavBar {{
    background-color: {Color.SURFACE};
    border-right: 1px solid {Color.BORDER};
}}
QLabel#NavSection {{
    color: {Color.TEXT_FAINT};
    font-size: {Font.SIZE_XS};
    font-weight: {Font.WEIGHT_SEMIBOLD};
    letter-spacing: 1px;
    padding: 4px 10px;
}}
QPushButton#NavButton {{
    background-color: transparent;
    color: {Color.TEXT_MUTED};
    border: none;
    border-radius: {Size.RADIUS_MD}px;
    padding: 8px 12px;
    text-align: left;
    font-size: {Font.SIZE_MD};
    font-weight: {Font.WEIGHT_MEDIUM};
}}
QPushButton#NavButton:hover {{
    background-color: {Color.SURFACE_HOVER};
    color: {Color.TEXT};
}}
QPushButton#NavButton[active="true"] {{
    background-color: {Color.ACCENT_SUBTLE};
    color: {Color.TEXT};
}}
"""


FILTER_BAR_QSS = f"""
QWidget#FilterBar {{
    background-color: {Color.SURFACE};
    border-bottom: 1px solid {Color.BORDER};
}}
QWidget#FilterBar QLabel {{
    color: {Color.TEXT_MUTED};
    font-size: {Font.SIZE_SM};
}}
"""


# Reusable button "kinds"
def primary_button_qss() -> str:
    return f"""
        QPushButton {{
            background-color: {Color.ACCENT};
            color: {Color.TEXT_INVERSE};
            border: none;
            border-radius: {Size.RADIUS_SM}px;
            padding: 6px 14px;
            font-weight: {Font.WEIGHT_SEMIBOLD};
        }}
        QPushButton:hover {{ background-color: {Color.ACCENT_HOVER}; }}
        QPushButton:pressed {{ background-color: {Color.ACCENT}; }}
    """


def ghost_button_qss() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {Color.TEXT_MUTED};
            border: 1px solid transparent;
            border-radius: {Size.RADIUS_SM}px;
            padding: 5px 10px;
            font-size: {Font.SIZE_SM};
        }}
        QPushButton:hover {{
            color: {Color.TEXT};
            background-color: {Color.SURFACE_HOVER};
        }}
    """


def danger_button_qss() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {Color.DANGER};
            border: 1px solid {Color.BORDER};
            border-radius: {Size.RADIUS_SM}px;
            padding: 5px 12px;
        }}
        QPushButton:hover {{
            background-color: rgba(238, 107, 110, 0.12);
            border-color: {Color.DANGER};
        }}
    """


def card_qss(accent: str | None = None, scenario_color: str | None = None,
             selected: bool = False, compact: bool = False) -> str:
    """Style for a Kanban card / item card."""
    if selected:
        border = f"1px solid {Color.ACCENT}"
        bg = Color.SURFACE_ACTIVE
    elif accent:
        border = f"1px solid {accent}"
        bg = Color.SURFACE_ALT
    else:
        border = f"1px solid {Color.BORDER}"
        bg = Color.SURFACE_ALT
    left_border = f"3px solid {scenario_color}" if scenario_color else "3px solid transparent"
    padding = "8px 10px" if compact else "10px 12px"
    font_size = Font.SIZE_SM if compact else Font.SIZE_MD
    return (
        f"background-color: {bg}; color: {Color.TEXT}; "
        f"border-radius: {Size.RADIUS_MD}px; padding: {padding}; "
        f"font-size: {font_size}; border: {border}; border-left: {left_border};"
    )


def column_header_qss(color: str) -> str:
    """Kanban column header — colored accent strip on top."""
    return (
        f"background-color: {Color.SURFACE}; color: {Color.TEXT}; "
        f"border: 1px solid {Color.BORDER}; border-top: 2px solid {color}; "
        f"border-radius: {Size.RADIUS_MD}px; padding: 8px 12px; "
        f"font-size: {Font.SIZE_SM}; font-weight: {Font.WEIGHT_SEMIBOLD};"
    )


def column_body_qss() -> str:
    return (
        f"background-color: {Color.SURFACE}; "
        f"border: 1px solid {Color.BORDER}; "
        f"border-radius: {Size.RADIUS_MD}px;"
    )


def chip_qss(color: str = Color.TEXT_MUTED) -> str:
    """Small inline tag/chip."""
    return (
        f"background-color: {Color.SURFACE_ALT}; color: {color}; "
        f"border: 1px solid {Color.BORDER}; "
        f"border-radius: 10px; padding: 2px 8px; "
        f"font-size: {Font.SIZE_XS}; font-weight: {Font.WEIGHT_MEDIUM};"
    )


def section_title_qss() -> str:
    return (
        f"color: {Color.TEXT_MUTED}; "
        f"font-size: {Font.SIZE_XS}; "
        f"font-weight: {Font.WEIGHT_SEMIBOLD}; "
        f"letter-spacing: 1px;"
    )


# ---------------------------------------------------------------------------
# Legacy alias — main.py imports _APP_STYLE from main_window. We keep it
# exported there for backward compatibility (see main_window.py).
# ---------------------------------------------------------------------------
__all__ = [
    "Color",
    "Size",
    "Font",
    "APP_STYLE",
    "TOP_BAR_QSS",
    "NAV_BAR_QSS",
    "FILTER_BAR_QSS",
    "primary_button_qss",
    "ghost_button_qss",
    "danger_button_qss",
    "card_qss",
    "column_header_qss",
    "column_body_qss",
    "chip_qss",
    "section_title_qss",
]
