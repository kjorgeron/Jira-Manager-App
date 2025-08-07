import functools
import tkinter as tk
from getpass import getuser
from jira_manager.utils import (
    create_toolbar,
    toolbar_action,
    create_divider,
    get_theme_mode,
    initialize_window,
    safe_button_action,
)
from jira_manager.custom_widgets import EntryWithPlaceholder
from jira_manager.themes import light_mode, dark_mode, ThemeManager
from tkinter import ttk
from jira_manager.custom_panels import (
    ConfigurationFormBuilder,
    TicketDisplayBuilder,
    switch_panel,
    ErrorMessageBuilder
)
from jira_manager.sql_manager import run_sql_stmt
from jira_manager.sql import tickets_table, fields_table
from multiprocessing import Queue
from threading import Event
from jira_manager.custom_widgets import TicketCard


def _set_cursor(event, widget, cursor):
    widget.configure(cursor=cursor)


def set_combobox_cursors(widget):
    for child in widget.winfo_children():
        if isinstance(child, ttk.Combobox):
            child.bind(
                "<Enter>", functools.partial(_set_cursor, widget=child, cursor="hand2")
            )
            child.bind(
                "<Leave>", functools.partial(_set_cursor, widget=child, cursor="")
            )
        else:
            set_combobox_cursors(child)


def set_button_cursors(widget):
    for child in widget.winfo_children():
        if isinstance(child, tk.Button):
            child.bind(
                "<Enter>", functools.partial(_set_cursor, widget=child, cursor="hand2")
            )
            child.bind(
                "<Leave>", functools.partial(_set_cursor, widget=child, cursor="")
            )
        else:
            set_button_cursors(child)


def enter_key_clear_focus_run_btn_event(
    root,
    payload,
    ui_state,
    panel_choice,
    widget_registry,
    theme_manager,
    stop_flag,
    thread_count,
    run_count,
    card_retainer,
    selected_items,
):
    toolbar_action(
        payload,
        ui_state,
        panel_choice,
        widget_registry,
        theme_manager,
        stop_flag,
        thread_count,
        card_retainer,
        selected_items,
        root
    )
    root.focus_set()


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


def setup_ticket_panel(parent, theme_manager, card_retainer, selected_items):
    tickets = TicketDisplayBuilder(
        parent,
        theme_manager=theme_manager,
        tickets=card_retainer,
        selected_items=selected_items,
    )
    theme_manager.register(tickets, "frame")
    return tickets


def main():

    # SETUP OF DATABASE TABLES
    db_path = "jira_manager/tickets.db"
    run_sql_stmt(db_path, tickets_table, stmt_type="create")
    run_sql_stmt(db_path, fields_table, stmt_type="create")
    stop_flag = Event()

    # WINDOW INIT
    root = initialize_window()
    widget_registry = {}
    database_queue = []
    selected_items_for_update = []
    card_retainer = []
    stop_flag = Event()
    # JQL queue and worker state
    from queue import Queue
    JQL_TASK_QUEUE = Queue()
    JQL_WORKER_RUNNING = False
    thread_count = 2  # Default value, adjust as needed
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
    theme_manager.register(error_panel, "frame")
    configure_panel = setup_configure_panel(root, theme_manager)
    ticket_panel = setup_ticket_panel(
        root, theme_manager, card_retainer, selected_items_for_update
    )

    # PANEL CHOICES

    panel_choice = {
        "error_panel": error_panel,
        "configure_panel": configure_panel,
        "ticket_panel": ticket_panel,
        "card_retainer": card_retainer,
    }

    panel_choice["ticket_panel"].set_panel_choice(panel_choice)
    panel_choice["configure_panel"].set_choices_for_selected_item_retention(
        panel_choice,
        ui_state,
        widget_registry,
        db_path,
        card_retainer,
        thread_count,
        selected_items_for_update,
    )

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
        command=lambda: safe_button_action(
            None,
            lambda: toolbar_action(
                {"type": "configure", "jql": ""},
                ui_state,
                panel_choice,
                widget_registry,
                theme_manager,
                stop_flag,
                JQL_TASK_QUEUE,
                JQL_WORKER_RUNNING,
                card_retainer,
                selected_items_for_update,
                root
            ),
            panel_choice=panel_choice,
        ),
    )
    config_btn.pack(side="left", padx=10)
    theme_manager.register(config_btn, "flashy_button")
    widget_registry["configure_btn"] = config_btn

    ticket_btn = tk.Button(
        toolbar,
        text="Ticket Butcket",
        command=lambda: safe_button_action(
            None,
            lambda: toolbar_action(
                {"type": "tickets", "jql": ""},
                ui_state,
                panel_choice,
                widget_registry,
                theme_manager,
                stop_flag,
                JQL_TASK_QUEUE,
                JQL_WORKER_RUNNING,
                card_retainer,
                selected_items_for_update,
                root
            ),
            panel_choice=panel_choice,
        ),
    )
    ticket_btn.pack(side="left", padx=10)
    theme_manager.register(ticket_btn, "base_button")

    jql_search_btn = tk.Button(
        toolbar,
        text="Search Jira",
        command=lambda: safe_button_action(
            None,
            lambda: toolbar_action(
                {"type": "search_jiras", "jql": jql_search.get()},
                ui_state,
                panel_choice,
                widget_registry,
                theme_manager,
                stop_flag,
                JQL_TASK_QUEUE,
                JQL_WORKER_RUNNING,
                card_retainer,
                selected_items_for_update,
                root
            ),
            panel_choice=panel_choice,
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
    jql_search.bind(
        "<Return>",
        lambda event: enter_key_clear_focus_run_btn_event(
            root,
            {"type": "search_jiras", "jql": jql_search.get()},
            ui_state,
            panel_choice,
            widget_registry,
            theme_manager,
            stop_flag,
            thread_count,
            card_retainer,
            selected_items_for_update,
            root,
        ),
    )

    # DIVIDER
    create_divider(root, theme_manager)

    # WELCOME LABEL
    welcome_label = tk.Label(
        root,
        text=f"Welcome {getuser()}, let's manage some jira tickets!",
        justify="center",
        font=("Trebuchet MS", 20, "bold"),
    )

    theme_manager.register(welcome_label, "label")
    widget_registry["welcome_label"] = welcome_label

    set_button_cursors(root)
    set_combobox_cursors(root)


    # SET STARTER PANEL
    ticket_bucket = run_sql_stmt(db_path, "SELECT * FROM tickets", stmt_type="select")
    if not ticket_bucket:
            panel_choice["error_panel"].update_message("No tickets stored in local database.\nPlease configure your Jira connection and fetch tickets.")
            switch_panel("error_panel", ui_state, panel_choice, widget_registry)
    else:
        root.after(
            100,
            lambda: switch_panel(
                "ticket_panel",
                ui_state,
                panel_choice,
                widget_registry,
                db_path,
                theme_manager,
                card_retainer,
                selected_items_for_update,
            ),
        )

    def on_configure(event):
        theme_manager.register(root, "root")
        theme_manager.register(panel_choice["ticket_panel"], "frame")
        theme_manager.register(panel_choice["configure_panel"], "frame")
        theme_manager.register(panel_choice["error_panel"], "frame")
        # Optionally, reapply to all major frames/widgets if needed

    root.bind("<Configure>", on_configure)

    root.mainloop()


if __name__ == "__main__":
    main()
