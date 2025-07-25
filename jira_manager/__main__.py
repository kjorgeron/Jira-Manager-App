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
    clear_focus,
    core_handler,
)
from jira_manager.custom_widgets import EntryWithPlaceholder
from jira_manager.themes import light_mode, dark_mode, ThemeManager
from jira_manager.file_manager import save_data, get_config_path
from tkinter import ttk
from jira_manager.custom_panels import (
    ConfigurationFormBuilder,
    ErrorMessageBuilder,
    TicketDisplayBuilder,
    switch_panel
)
from jira_manager.sql_manager import table_exists, create_table, run_sql_stmt
from jira_manager.sql import tickets_table, fields_table
from multiprocessing import Queue
from threading import Thread, Event
from time import sleep
from jira_manager.file_manager import load_data


def on_close(stop_flag, root):
    stop_flag.set()  # signal the thread to stop
    root.destroy()  # close the UI


def setup_configure_panel(parent, theme_manager):
    config = ConfigurationFormBuilder(
        parent,
        dark_mode=dark_mode,
        light_mode=light_mode,
        theme_manager=theme_manager,
        padx=10,
        pady=10,
    )
    config_form = config.build_form()
    config_form.pack(expand=True, fill="both")
    theme_manager.register(config, "frame")
    theme_manager.register(config_form, "frame")
    return config


def setup_ticket_panel(parent, theme_manager):
    tickets = TicketDisplayBuilder(parent, theme_manager=theme_manager)
    # ticket_bucket = tickets.build_ticket_board()
    # ticket_bucket.pack(expand=True, fill="both")
    theme_manager.register(tickets, "frame")
    # theme_manager.register(ticket_bucket, "frame")
    return tickets


def main():

    # SETUP OF DATABASE TABLES
    db_path = "jira_manager/tickets.db"
    run_sql_stmt(db_path, tickets_table, stmt_type="create")
    run_sql_stmt(db_path, fields_table, stmt_type="create")

    # WINDOW INIT
    root = initialize_window()
    widget_registry = {}
    database_queue = []
    jira_queue = []
    stop_flag = Event()
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(stop_flag, root))

    def clear_focus(event):
        widget_class = str(event.widget.winfo_class())
        allowed_classes = (
            "Entry",
            "TEntry",
            "TCombobox",
            "Text",
            "Custom.TCombobox",
            "Listbox",
            # "Button",
            "Checkbutton",
            "Radiobutton",
        )
        if widget_class not in allowed_classes:
            root.focus_set()

    if root.winfo_exists():
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
    ticket_panel = setup_ticket_panel(root, theme_manager)

    # PANEL CHOICES
    panel_choice = {
        "error_panel": error_panel,
        "configure_panel": configure_panel,
        "ticket_panel": ticket_panel,
    }

    # APP LOGO
    logo_frame = tk.Frame(root, height=60)
    logo_frame.pack(fill=tk.X)

    theme_manager.register(logo_frame, "frame")

    logo_label = tk.Label(
        logo_frame,
        text=" ⚒️ TicketSmith",
        font=("Trebuchet MS", 25, "bold"),
    )
    logo_label.pack(pady=5, side="left")

    theme_manager.register(logo_label, "label")

    # TOOLBAR
    toolbar = create_toolbar(root, mode["background"])
    toolbar.pack()
    theme_manager.register(toolbar, "frame")

    config_btn = tk.Button(
        toolbar,
        text="Configure",
        command=lambda: toolbar_action(
            {"type": "configure", "jql": ""},
            ui_state,
            panel_choice,
            widget_registry,
            database_queue,
        ),
    )
    config_btn.pack(side="left", padx=10)
    theme_manager.register(config_btn, "flashy_button")

    ticket_btn = tk.Button(
        toolbar,
        text="Ticket Butcket",
        command=lambda: toolbar_action(
            {"type": "tickets", "jql": ""},
            ui_state,
            panel_choice,
            widget_registry,
            database_queue,
        ),
    )
    ticket_btn.pack(side="left", padx=10)
    theme_manager.register(ticket_btn, "base_button")

    jql_search_btn = tk.Button(
        toolbar,
        text="Search Jira",
        command=lambda: toolbar_action(
            {"type": "search_jiras", "jql": jql_search.get()},
            ui_state,
            panel_choice,
            widget_registry,
            database_queue,
        ),
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
    widget_registry["jql_query"] = jql_search

    # DIVIDER
    create_divider(root, mode["muted_text"])

    # WELCOME LABEL
    welcome_label = tk.Label(
        root,
        text=f"Welcome {getuser()}, let's manage some jira tickets!",
        justify="center",
        font=("Trebuchet MS", 20, "bold"),
    )
   
    theme_manager.register(welcome_label, "label")
    widget_registry["welcome_label"] = welcome_label
    # sleep(1)

    # info_frame = tk.Frame(root, padx=10, pady=10)
    # info_frame.pack(fill="x")
    # theme_manager.register(info_frame, "frame")
    # info_message = tk.Label(info_frame, text="Thanks for choosing Ticket Smith by Dead Viking Software.\nFeel free to request new features via the request feature button.", justify="center")
    # theme_manager.register(info_message, "label")
    # info_message.pack(padx=10, pady=10)

    # START WATCHER THREADS
    core_watcher = Thread(target=core_handler, args=(stop_flag, database_queue, db_path, jira_queue, ui_state, panel_choice, widget_registry), daemon=True)
    core_watcher.start()

    root.mainloop()

if __name__ == "__main__":
    main()
