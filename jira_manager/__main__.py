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


# CONFIG INIT
if not os.path.exists(get_config_path()):
    save_data({"theme": "Dark"})

# SETUP THEME CHOICE
mode = get_theme_mode(config_path="jira_manager/app_config.json")
try:
    if mode.lower() == "light":
        mode = light_mode
    elif mode.lower() == "dark":
        mode = dark_mode
except Exception:
    mode = dark_mode


# WINDOW INIT
root = (
    initialize_window()
)  # NEED TO FIX DYNAMIC THEME CHANGE ... WILL USE NEW CLASS IN THEMES.PY

# THEME MANAGER
theme_manager = ThemeManager(root=root, theme=mode)

theme_manager.register(root, "root")

# CONFIGURE COMBOBOX
style = ttk.Style()

theme_manager.register(style, "combobox")
# style.configure(
#     "Custom.TCombobox",
#     foreground=mode["primary_color"],  # Text color
#     fieldbackground=mode["background"],  # Field background
# )

# # Use `map` to control dropdown popup on hover/active/etc
# style.map(
#     "Custom.TCombobox",
#     fieldbackground=[("readonly", mode["background"])],
#     foreground=[("readonly", mode["primary_color"])],
# )


# APP LOGO
logo_frame = tk.Frame(root, bg=mode["background"], height=60)
logo_frame.pack(fill=tk.X)

theme_manager.register(logo_frame, "frame")

logo_label = tk.Label(
    logo_frame,
    text=" 🛠️TicketSmith",
    font=("Arial", 22, "bold"),
    # bg=mode["background"],
    # fg="#D2691E",  # Burnt Copper
)
logo_label.pack(pady=5, side="left")

theme_manager.register(logo_label, "label")

# TOOLBAR
toolbar = create_toolbar(root, mode["background"])
toolbar.pack()
theme_manager.register(toolbar, "frame")
ui_state = {"active_panel": None}

app_logo = tk.Frame(toolbar)

tk.Button(
    toolbar,
    text="Configure",
    font=("Trebuchet MS", 12, "bold"),
    bg=mode["primary_color"],
    fg="white",
    activebackground=mode["btn_highlight"],  # Hover color
    activeforeground="white",
    command=lambda: toolbar_action(
        root, {"type": "configure", "jql": ""}, ui_state, mode, theme_manager
    ),
).pack(side="left", padx=10)


tk.Button(
    toolbar,
    text="Search Jira",
    font=("Trebuchet MS", 12, "bold"),
    bg=mode["btn_highlight"],
    fg="white",
    activebackground=mode["primary_color"],  # Hover color
    activeforeground="white",
    command=lambda: toolbar_action(
        root,
        {"type": "search_jiras", "jql": jql_search.get()},
        ui_state,
        mode,
        theme_manager,
    ),
).pack(side="left", padx=10)

jql_search = EntryWithPlaceholder(
    toolbar,
    placeholder="Enter proper JQL query",
    initial_text="",
    font=("Arial", 14, "bold"),
    width=25,
    color=mode["btn_highlight"],
    # highlightbackground=mode["primary_color"],  # Burnt Copper (unfocused)
    # highlightcolor=mode["btn_highlight"],  # Forge Gold (focused)
    # highlightthickness=2,
    # bd=0,
    # relief=tk.FLAT,
    # bg=mode["background"],
    # fg=mode["primary_color"],
)
jql_search.pack(side="left", padx=10)
theme_manager.register(jql_search, "placeholder_entry")

# DIVIDER
create_divider(root, mode["muted_text"])

# WELCOME LABEL
try:
    welcome_label = tk.Label(
        root,
        text=f"Welcome {getuser()}, let's manage some jira's! ",
        font=("Trebuchet MS", 14, "bold"),
        # bg=mode["background"],
        # fg=mode["secondary_color"],
        width=50,
        wraplength=400,
    )
except:
    welcome_label = tk.Label(
        root,
        text="Welcome, let's manage some jira's!",
        font=("Trebuchet MS", 12, "bold"),
        width=50,
        wraplength=400,
    )
welcome_label.pack(pady=10)
theme_manager.register(welcome_label, "label")


# CLEAR ENTRY FOCUS EVENT
def clear_focus(event):
    # Only clear if the clicked widget is NOT an Entry (or subclass of Entry)
    if not isinstance(event.widget, tk.Entry):
        event.widget.focus_set()  # give focus to whatever was clicked
        root.focus_set()  # or default to root if needed


# Bind all clicks to trigger focus logic
root.bind_all("<Button-1>", clear_focus, add="+")


# RUN APP
root.mainloop()
