import tkinter as tk
import os
from PIL import Image, ImageTk
from getpass import getuser
from jira_manager.utils import (
    create_toolbar,
    toolbar_action,
    create_divider,
    get_theme_mode,
    initialize_window,
)
from jira_manager.custom_widgets import EntryWithPlaceholder
from jira_manager.themes import light_mode, dark_mode, ThemeManager
from jira_manager.file_manager import save_data, get_config_path
from tkinter import ttk
from jira_manager.custom_panels import ConfigurationFormBuilder, ErrorMessageBuilder


def setup_configure_panel(parent, theme_manager):
    config = ConfigurationFormBuilder(parent, dark_mode=dark_mode, light_mode=light_mode, theme_manager=theme_manager, padx=10, pady=10)
    config_form = config.build_form()
    config_form.pack(expand=True, fill="both")
    theme_manager.register(config, "frame")
    theme_manager.register(config_form, "frame")
    return config


def main():
    # WINDOW INIT
    root = (
        initialize_window()
    )

    def clear_focus(event):
        widget = event.widget
        if not isinstance(widget, (tk.Entry, ttk.Entry)):
            root.focus_set()

    root.bind_all("<Button-1>", clear_focus)


    # SETUP THEME CHOICE
    mode = get_theme_mode(config_path="jira_manager/app_config.json")
    try:
        if mode.lower() == "light":
            mode = light_mode
        elif mode.lower() == "dark":
            mode = dark_mode
    except Exception:
        mode = dark_mode

    # THEME MANAGER
    theme_manager = ThemeManager(root=root, theme=mode)
    theme_manager.register(root, "root")
    ui_state = {"active_panel": None}

    error_panel = ErrorMessageBuilder(root, theme_manager)
    configure_panel = setup_configure_panel(root, theme_manager)

    panel_choice = {
        "error_panel": error_panel,
        "configure_panel": configure_panel,
    }

    # TOOLBAR
    toolbar = create_toolbar(root, mode["background"])
    toolbar.pack()
    theme_manager.register(toolbar, "frame")

    config_btn = tk.Button(
        toolbar,
        text="Configure",
        command=lambda: toolbar_action(
            root, {"type": "configure", "jql": ""}, ui_state, "mode", theme_manager, None, panel_choice
        )
    )
    config_btn.pack(side="left", padx=10)
    theme_manager.register(config_btn, "conf_button")

    jql_search_btn = tk.Button(
        toolbar,
        text="Search Jira",
        command=lambda: toolbar_action(
            root, {"type": "search_jiras", "jql": jql_search.get()}, ui_state, "mode", theme_manager, None, panel_choice
        )
    )
    jql_search_btn.pack(side="left", padx=10)
    theme_manager.register(jql_search_btn, "base_button")

    jql_search = EntryWithPlaceholder(
        toolbar,
        placeholder="Enter proper JQL query",
        initial_text="",
        width=25,
    )
    jql_search.pack(side="left", padx=10)
    theme_manager.register(jql_search, "placeholder_entry")

    # DIVIDER
    create_divider(root, mode["muted_text"])

    # Show default panel
    # configure_panel.pack(fill="both", expand=True)
    # ui_state["active_panel"] = configure_panel

    root.mainloop()

if __name__ == "__main__":
    main()
