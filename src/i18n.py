"""
Lightweight runtime localization helpers (English + Simplified Chinese).
"""

from __future__ import annotations

from PyQt6.QtCore import QLocale

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
        "language.system": "System Default",
        "language.english": "English",
        "language.chinese": "中文（简体）",
        "settings.general": "General",
        "settings.data": "Data Management",
        "settings.ai": "AI Agent",
        "settings.mcp": "MCP Client",
        "settings.calendar": "Calendar Sync",
        "settings.hotkeys": "Hotkeys",
        "settings.performance": "Performance",
        "settings.updates": "Updates",
        "settings.restart_hint": "Restart the app to apply language changes everywhere.",
        "ai.provider": "Provider:",
        "ai.provider.openai": "OpenAI / GPT",
        "ai.provider.anthropic": "Anthropic / Claude",
        "ai.provider.gemini": "Google / Gemini",
        "ai.provider.openrouter": "OpenRouter",
        "ai.provider.local": "Local / Open-source",
        "ai.provider.custom": "OpenAI-compatible / Custom",
        "ai.base_url": "Base URL:",
        "ai.base_url.hint": "Leave blank for hosted APIs; enter an OpenAI-compatible endpoint for OpenRouter or local models.",
        "ai.model.help": "Examples: gpt-4o-mini, claude-3-5-sonnet-latest, gemini/gemini-1.5-pro, openrouter/deepseek/deepseek-chat",
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
        "language.system": "系统默认",
        "language.english": "English",
        "language.chinese": "中文（简体）",
        "settings.general": "常规",
        "settings.data": "数据管理",
        "settings.ai": "AI 代理",
        "settings.mcp": "MCP 客户端",
        "settings.calendar": "日历同步",
        "settings.hotkeys": "快捷键",
        "settings.performance": "性能",
        "settings.updates": "更新",
        "settings.restart_hint": "语言变更后请重启应用以在所有界面生效。",
        "ai.provider": "提供方：",
        "ai.provider.openai": "OpenAI / GPT",
        "ai.provider.anthropic": "Anthropic / Claude",
        "ai.provider.gemini": "Google / Gemini",
        "ai.provider.openrouter": "OpenRouter",
        "ai.provider.local": "本地 / 开源",
        "ai.provider.custom": "OpenAI 兼容 / 自定义",
        "ai.base_url": "基础地址：",
        "ai.base_url.hint": "云端 API 可留空；OpenRouter 或本地模型请填写 OpenAI 兼容端点。",
        "ai.model.help": "示例：gpt-4o-mini、claude-3-5-sonnet-latest、gemini/gemini-1.5-pro、openrouter/deepseek/deepseek-chat",
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
    if language.startswith("system"):
        return system_language()
    return "zh" if language.startswith("zh") else "en"


def system_language() -> str:
    locale_name = QLocale.system().name().lower()
    if locale_name.startswith("zh"):
        return "zh"
    return "en"


def language_choices() -> list[tuple[str, str]]:
    return [
        ("system", tr("language.system", "System Default")),
        ("en", tr("language.english", "English")),
        ("zh", tr("language.chinese", "中文（简体）")),
    ]


def tr(key: str, default: str | None = None, **kwargs) -> str:
    language = current_language()
    text = _TRANSLATIONS.get(language, {}).get(
        key, _TRANSLATIONS["en"].get(key, default if default is not None else key)
    )
    if kwargs:
        return text.format(**kwargs)
    return text
