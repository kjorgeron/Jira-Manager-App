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
from jira_manager.themes import light_mode, dark_mode
from jira_manager.file_manager import save_data, get_config_path
from tkinter import ttk


# CONFIG INIT
if not os.path.exists(get_config_path()):
    save_data({"theme": "Dark"})


# SETUP THEME
mode = get_theme_mode(config_path="jira_manager/app_config.json")
# print(f"{mode=}")
try:
    if mode == "Light":
        mode = light_mode
    elif mode == "Dark":
        mode = dark_mode
except Exception:
    mode = dark_mode

print(f"{mode=}")

# WINDOW INIT
root = initialize_window(mode["background"])

# CONFIGURE COMBOBOX
style = ttk.Style()
style.theme_use("default")
style.configure(
    "Custom.TCombobox",
    foreground=mode["primary_color"],   # Text color
    fieldbackground=mode["background"], # Field background
)

# Use `map` to control dropdown popup on hover/active/etc
style.map(
    "Custom.TCombobox",
    fieldbackground=[("readonly", mode["background"])],
    foreground=[("readonly", mode["primary_color"])],
)





# APP LOGO
logo_frame = tk.Frame(root, bg=mode["background"], height=60)
logo_frame.pack(fill=tk.X)

logo_label = tk.Label(
    logo_frame,
    text=" 🛠️TicketSmith",
    font=("Arial", 22, "bold"),
    bg=mode["background"],
    fg="#D2691E",  # Burnt Copper
)
logo_label.pack(pady=5, side="left")


# TOOLBAR
toolbar = create_toolbar(root, mode["background"])
toolbar.pack()
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
        root, {"type": "configure", "jql": ""}, ui_state, mode
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
        root, {"type": "search_jiras", "jql": jql_search.get()}, ui_state, mode
    ),
).pack(side="left", padx=10)

jql_search = EntryWithPlaceholder(
    toolbar,
    placeholder="Enter proper JQL query",
    color=mode["btn_highlight"],
    initial_text=None,
    font=("Arial", 14, "bold"),
    width=25,
    highlightbackground=mode["primary_color"],  # Burnt Copper (unfocused)
    highlightcolor=mode["btn_highlight"],  # Forge Gold (focused)
    highlightthickness=2,
    bd=0,
    relief=tk.FLAT,
    bg=mode["background"],
    fg=mode["primary_color"],
)
jql_search.pack(side="left", padx=10)

# DIVIDER
create_divider(root, mode["muted_text"])

# WELCOME LABEL
try:
    test_label = tk.Label(
        root,
        text=f"Welcome {getuser()}, let's manage some jira's! ",
        font=("Trebuchet MS", 14, "bold"),
        bg=mode["background"],
        fg=mode["secondary_color"],
        width=50,
        wraplength=400,
    )
except:
    test_label = tk.Label(
        root,
        text="Welcome, let's manage some jira's!",
        font=("Trebuchet MS", 12, "bold"),
        width=50,
        wraplength=400,
    )
test_label.pack(pady=10)

# RUN APP
root.mainloop()
