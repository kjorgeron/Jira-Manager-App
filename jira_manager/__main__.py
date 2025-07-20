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

# def setup_error_panel(parent):
#     error = ErrorMessageBuilder(parent, theme_manager=theme_manager)
#     theme_manager.register(error, "frame")
#     return error

# # CONFIG INIT
# if not os.path.exists(get_config_path()):
#     save_data({"theme": "Dark"})

# # SETUP THEME CHOICE
# mode = get_theme_mode(config_path="jira_manager/app_config.json")
# try:
#     if mode.lower() == "light":
#         mode = light_mode
#     elif mode.lower() == "dark":
#         mode = dark_mode
# except Exception:
#     mode = dark_mode

# # THEME MANAGER
# theme_manager = ThemeManager(root=root, theme=mode)

# # WINDOW INIT
# root = (
#     initialize_window()
# )  # NEED TO FIX DYNAMIC THEME CHANGE ... WILL USE NEW CLASS IN THEMES.PY


# theme_manager.register(root, "root")

# # # CONFIGURE COMBOBOX
# # style = ttk.Style()

# # theme_manager.register(style, "combobox")
# # style.configure(
# #     "Custom.TCombobox",
# #     foreground=mode["primary_color"],  # Text color
# #     fieldbackground=mode["background"],  # Field background
# # )

# # # Use `map` to control dropdown popup on hover/active/etc
# # style.map(
# #     "Custom.TCombobox",
# #     fieldbackground=[("readonly", mode["background"])],
# #     foreground=[("readonly", mode["primary_color"])],
# # )


# # APP LOGO
# logo_frame = tk.Frame(root, height=60)
# logo_frame.pack(fill=tk.X)

# theme_manager.register(logo_frame, "frame")

# logo_label = tk.Label(
#     logo_frame,
#     text=" 🛠️TicketSmith",
#     font=("Arial", 22, "bold"),
# )
# logo_label.pack(pady=5, side="left")

# theme_manager.register(logo_label, "label")

# # TOOLBAR
# toolbar = create_toolbar(root, mode["background"])
# toolbar.pack()
# theme_manager.register(toolbar, "frame")
# ui_state = {"active_panel": None}
# panel_choice = {
#     "configure_panel": setup_configure_panel(root),
#     "error_panel": setup_error_panel(root)
# }

# app_logo = tk.Frame(toolbar)
# active_panels = []

# config_btn = tk.Button(
#     toolbar,
#     text="Configure",
#     command=lambda: toolbar_action(
#         root, {"type": "configure", "jql": ""}, ui_state, mode, theme_manager, active_panels, panel_choice
#     ),
# )
# config_btn.pack(side="left", padx=10)
# theme_manager.register(config_btn, "conf_button")

# jql_search_btn = tk.Button(
#     toolbar,
#     text="Search Jira",
#     command=lambda: toolbar_action(
#         root,
#         {"type": "search_jiras", "jql": jql_search.get()},
#         ui_state,
#         mode,
#         theme_manager,
#         active_panels,
#         panel_choice
#     ),
# )
# jql_search_btn.pack(side="left", padx=10)
# theme_manager.register(jql_search_btn, "base_button")

# jql_search = EntryWithPlaceholder(
#     toolbar,
#     placeholder="Enter proper JQL query",
#     initial_text="",
#     width=25,
# )
# jql_search.pack(side="left", padx=10)
# theme_manager.register(jql_search, "placeholder_entry")

# # DIVIDER
# create_divider(root, mode["muted_text"])

# # WELCOME LABEL
# try:
#     welcome_label = tk.Label(
#         root,
#         text=f"Welcome {getuser()}, let's manage some jira's! ",
#         font=("Trebuchet MS", 14, "bold"),
#         # bg=mode["background"],
#         # fg=mode["secondary_color"],
#         width=50,
#         wraplength=400,
#     )
# except:
#     welcome_label = tk.Label(
#         root,
#         text="Welcome, let's manage some jira's!",
#         font=("Trebuchet MS", 12, "bold"),
#         width=50,
#         wraplength=400,
#     )
# welcome_label.pack(pady=10)
# theme_manager.register(welcome_label, "label")


# # CLEAR ENTRY FOCUS EVENT
# def clear_focus(event):
#     # Only clear if the clicked widget is NOT an Entry (or subclass of Entry)
#     if not isinstance(event.widget, tk.Entry):
#         event.widget.focus_set()  # give focus to whatever was clicked
#         root.focus_set()  # or default to root if needed


# # Bind all clicks to trigger focus logic
# root.bind_all("<Button-1>", clear_focus, add="+")


# # RUN APP
# root.mainloop()

# import tkinter as tk
# from jira_manager.custom_panels import ErrorMessageBuilder
# from panels.configure_panel import setup_configure_panel  # You’ll define this
# from theme_manager import ThemeManager
# from utils import toolbar_action

def main():
    # WINDOW INIT
    root = (
        initialize_window()
    )

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
