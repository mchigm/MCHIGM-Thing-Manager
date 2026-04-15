"""
Lightweight runtime localization helpers (English + Simplified Chinese).
"""

from __future__ import annotations

from src.settings_store import load_settings

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app.name": "MCHIGM Thing Manager",
        "top.workspace": "Workspace:",
        "top.search.placeholder": "Search items, #tags, natural language…",
        "top.filters": "🔍 Filters",
        "top.settings": "⚙ Settings",
        "nav.todos": "✅  TODOs",
        "nav.timetable": "📅  Timetable",
        "nav.memo": "💬  MEMO",
        "nav.plan": "🗺   Plan",
        "settings.title": "Settings",
        "settings.language": "Language:",
        "language.english": "English",
        "language.chinese": "中文（简体）",
        "memo.install_cli": "Install CLI",
        "memo.install_cli.title": "Install OpenClaw CLI",
        "memo.install_cli.confirm": "Install OpenClaw CLI using pip now?",
        "memo.install_cli.success": "OpenClaw CLI installed successfully.",
        "memo.install_cli.fail": "OpenClaw CLI installation failed.",
        "period.enable": "Period filter",
        "period.start": "From:",
        "period.end": "To:",
        "period.mode.overlap": "Overlap",
        "period.mode.exact": "Inside only",
    },
    "zh": {
        "app.name": "MCHIGM 事务管理器",
        "top.workspace": "工作区：",
        "top.search.placeholder": "搜索条目、#标签、自然语言…",
        "top.filters": "🔍 筛选",
        "top.settings": "⚙ 设置",
        "nav.todos": "✅  待办",
        "nav.timetable": "📅  时间表",
        "nav.memo": "💬  备忘",
        "nav.plan": "🗺   计划",
        "settings.title": "设置",
        "settings.language": "语言：",
        "language.english": "English",
        "language.chinese": "中文（简体）",
        "memo.install_cli": "安装 CLI",
        "memo.install_cli.title": "安装 OpenClaw CLI",
        "memo.install_cli.confirm": "现在使用 pip 安装 OpenClaw CLI 吗？",
        "memo.install_cli.success": "OpenClaw CLI 安装成功。",
        "memo.install_cli.fail": "OpenClaw CLI 安装失败。",
        "period.enable": "时间范围筛选",
        "period.start": "开始：",
        "period.end": "结束：",
        "period.mode.overlap": "有交集",
        "period.mode.exact": "仅完整落入",
    },
}


def current_language() -> str:
    language = str(load_settings().get("language", "en")).lower()
    return "zh" if language.startswith("zh") else "en"


def tr(key: str, default: str | None = None, **kwargs) -> str:
    language = current_language()
    text = _TRANSLATIONS.get(language, {}).get(
        key, _TRANSLATIONS["en"].get(key, default if default is not None else key)
    )
    if kwargs:
        return text.format(**kwargs)
    return text

