import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk
from jira_manager.themes import ThemeManager
from jira_manager.file_manager import load_data, save_data
from jira_manager.custom_widgets import EntryWithPlaceholder, TicketCard
from jira_manager.sql_manager import run_sql_stmt
from math import ceil
from jira_manager.thread_manager import SmartThread


def batch_list(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]


# def update_ticket_bucket_with_single(
#     ticket, panel_choice, theme_manager, selected_items, card_retainer=None
# ):
#     # print(f"{panel_choice=}")  # Debug print commented out
#     base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")
#     card = TicketCard(
#         ticket,
#         theme_manager,
#         master=base_frame,
#         selected_items=selected_items,
#         card_retainer=card_retainer,
#     )
#     # print(f"{ticket=} from update_ticket_bucket_with_single")
#     card.update_panel_choice(panel_choice=panel_choice)
#     if ticket["key"] in selected_items:
#         card.set_bg(theme_manager.theme["pending_color"])
#         card.widget_registry.get("select_btn").config(
#             text="Unselect", bg=theme_manager.theme["pending_color"]
#         )
#     # Always pack at the bottom for correct order
#     card.pack(side="top", fill="x", padx=5, pady=3, expand=True)


# def update_ticket_bucket(
#     ticket_bucket_items, panel_choice, theme_manager, selected_items, card_retainer=None
# ):
#     base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")

#     # Remove all existing ticket widgets from the base_frame
#     for child in base_frame.winfo_children():
#         child.destroy()

#     max_cols = 5
#     # print(f"{ticket_bucket_items=}")
#     # Make columns expandable
#     for col in range(max_cols):
#         base_frame.columnconfigure(col, weight=1)
#     for index, item in enumerate(ticket_bucket_items):
#         row = index // max_cols
#         col = index % max_cols
#         update_ticket_bucket_with_single(
#             item,
#             panel_choice,
#             theme_manager,
#             selected_items,
#             card_retainer=card_retainer,
#         )


def get_page_contents(page_number):
    if page_number == 1:
        return (1, 50)
    elif page_number > 1:
        start = (page_number - 1) * 50
        end = start + 50
        return (start, end)


def switch_panel(
    panel_key,
    ui_state,
    panel_choice,
    widget_registry,
    db_path: str = None,
    theme_manager: ThemeManager = None,
    card_retainer: list = None,
    selected_items: list = None,
):
    print(f"PANEL SWITCH -> {panel_key}")
    current = ui_state.get("active_panel")

    if current and current != panel_choice[panel_key]:
        current.pack_forget()
    next_panel = panel_choice[panel_key]

    # Handle welcome_label
    welcome_label = widget_registry.get("welcome_label")
    if panel_key == "error_panel":
        if welcome_label.winfo_ismapped():
            welcome_label.pack_forget()
        next_panel.pack(fill="x", padx=100, pady=10)

    # Handle receipts_panel: change welcome label and show panel
    elif panel_key == "receipts_panel":
        if welcome_label:
            welcome_label.config(text="Receipt Log")
            if not welcome_label.winfo_ismapped():
                welcome_label.pack(pady=10)
        next_panel.pack(fill="both", expand=True, padx=10, pady=10)

    # Handle configure button flicker: only enable/disable, never pack/forget
    configure_btn = (
        widget_registry.get("configure_btn")
        if widget_registry.get("configure_btn")
        else None
    )
    tickets_btn = (
        widget_registry.get("tickets_btn")
        if widget_registry.get("tickets_btn")
        else None
    )
    receipts_btn = (
        widget_registry.get("receipts_btn")
        if widget_registry.get("receipts_btn")
        else None
    )
    if configure_btn:
        configure_btn.config(state="normal")
    if receipts_btn:
        receipts_btn.config(state="normal")
    if tickets_btn:
        tickets_btn.config(state="normal")

    if panel_key == "configure_panel":
        if welcome_label.winfo_ismapped():
            welcome_label.pack_forget()
        if configure_btn:
            configure_btn.config(state="disabled")
        next_panel.pack(fill="both", expand=True, padx=10, pady=10)
        # Set focus to ticket panel canvas for instant mouse wheel scrolling
        try:
            canvas = panel_choice["ticket_panel"].widget_registry.get("canvas")
            if canvas:
                canvas.focus_set()
                print(
                    f"[DEBUG] Focused canvas: {canvas}, has focus: {canvas == canvas.focus_displayof()}"
                )
        except Exception as e:
            print(f"[DEBUG] Canvas focus error: {e}")
    elif panel_key == "ticket_panel":
        tickets_btn.config(state="disabled")
    elif panel_key == "receipts_panel":
        receipts_btn.config(state="disabled")

    if panel_key == "ticket_panel":
        if panel_choice.get("ticket_panel"):

            # if db_path:
            #     current_page = panel_choice["ticket_panel"].current_page

            #     try:
            #         # Initial load: get the first 50 tickets, newest first
            #         issues = run_sql_stmt(
            #             db_path,
            #             "SELECT * FROM tickets ORDER BY ticket_id DESC LIMIT 50;",
            #             stmt_type="select",
            #         )
            #         for issue in issues:
            #             print(f"ticket_id={issue[0]}, key={issue[1]}")
            #         if issues:
            #             last_id = issues[-1][0]  # ticket_id of the last ticket on this page
            #             panel_choice.get("ticket_panel").update_last_ticket_id(last_id)
            #             first_id = issues[0][
            #                 0
            #             ]  # ticket_id of the first ticket on this page
            #             panel_choice.get("ticket_panel").update_first_ticket_id(first_id)
            #             panel_choice["ticket_panel"].update_page_index(
            #                 current_page, (first_id, last_id)
            #             )

            #         else:
            #             last_id = None
            #         print(f"{len(issues)=} from panel switch")
            #         total_tickets = run_sql_stmt(
            #             db_path, "SELECT COUNT(*) FROM tickets", stmt_type="select"
            #         )
            #         print(f"{total_tickets[0][0]=}")
            #         show_issues = []
            #         for i, issue in enumerate(issues):
            #             show = {"key": issue[1]}
            #             if i < 50 and show not in show_issues:
            #                 show_issues.append(show)
            #         total_pages = ceil(total_tickets[0][0] / 50)
            #         panel_choice["ticket_panel"].widget_registry.get(
            #             "total_tickets"
            #         ).config(text=f"{total_pages}")
            #         print(f"{total_pages=}")
            #         panel_choice["ticket_panel"].update_total_pages(total_pages)

            #         update_ticket_bucket(
            #             show_issues,
            #             panel_choice,
            #             theme_manager,
            #             selected_items,
            #             card_retainer,
            #         )
            #     except Exception as e:
            #         print(f"Error loading tickets: {e}")
            #         pass
            panel_choice.get("ticket_panel").build()
            widget = widget_registry.get("welcome_label")
            widget.config(text="Ticket Bucket")
            if not widget.winfo_ismapped():
                widget.pack(fill="x", padx=5, pady=5)
            next_panel.pack(fill="both", expand=True, padx=10, pady=10)
    ui_state["active_panel"] = next_panel


class ConfigurationFormBuilder(tk.Frame):
    def __init__(
        self,
        master=None,
        cnf=None,
        *,
        background=None,
        bd=0,
        bg=None,
        border=0,
        borderwidth=0,
        class_="Frame",
        colormap="",
        container=False,
        cursor="",
        height=0,
        highlightbackground=None,
        highlightcolor=None,
        name=None,
        padx=0,
        pady=0,
        relief="flat",
        takefocus=0,
        visual="",
        width=0,
        theme_manager: ThemeManager = None,
        light_mode: dict = None,
        dark_mode: dict = None,
    ):
        super().__init__(
            master,
            cnf,
            background=background,
            bd=bd,
            bg=bg,
            border=border,
            borderwidth=borderwidth,
            class_=class_,
            colormap=colormap,
            container=container,
            cursor=cursor,
            height=height,
            highlightbackground=highlightbackground,
            highlightcolor=highlightcolor,
            name=name,
            padx=padx,
            pady=pady,
            relief=relief,
            takefocus=takefocus,
            visual=visual,
            width=width,
        )
        self.theme_manager = theme_manager
        self.config = load_data()
        self.font_style = ("Arial", 12, "bold")
        self.light_mode = light_mode
        self.dark_mode = dark_mode
        self.panel_choice = None
        self.ui_state = None
        self.widget_registry = None
        self.db_path = None
        self.card_retainer = None
        self.thread_count = None
        self.selected_items = None

    def set_choices_for_selected_item_retention(
        self,
        panel_choice,
        ui_state,
        widget_registry,
        db_path,
        card_retainer,
        thread_count,
        selected_items,
    ):
        self.panel_choice = panel_choice
        self.ui_state = ui_state
        self.widget_registry = widget_registry
        self.db_path = db_path
        self.card_retainer = card_retainer
        self.thread_count = thread_count
        self.selected_items = selected_items

    def build_form(self):

        # INTERNAL FUNCTIONS
        def get_clean_value(widget):
            value = widget.get()
            if value != widget.placeholder or widget["fg"] != widget.placeholder_color:
                return value
            return ""

        def on_save(theme_manager: ThemeManager):
            # Handles clearing of unused data for login
            if selected_auth.get() == "Basic Auth":
                token_input.delete(0, tk.END)
                token_input.reset_to_placeholder()
            else:  # Token Auth selected
                username_input.delete(0, tk.END)
                username_input.reset_to_placeholder()
                password_input.delete(0, tk.END)
                password_input.reset_to_placeholder()

            # Handles clearing of unused data for proxy
            if proxy_option.get() == "No":
                http_input.delete(0, tk.END)
                https_input.delete(0, tk.END)

            # Get previous thread count from config
            prev_thread_count = self.config.get("thread_count", "safe_mode")

            payload = {
                "server": get_clean_value(jira_server_input),
                "http_proxy": http_input.get(),
                "https_proxy": https_input.get(),
                "token": get_clean_value(token_input),
                "username": get_clean_value(username_input),
                "password": get_clean_value(password_input),
                "auth_type": selected_auth.get(),
                "proxy_option": proxy_option.get(),
                "theme": theme_option.get(),
            }
            tc_display = thread_count_option.get()
            tc_value = display_to_value.get(tc_display, tc_display)
            payload["thread_count"] = tc_value

            # SAVE PAYLOAD DATA
            save_data(payload)

            # If thread count changed, prompt for restart
            if str(tc_value) != str(prev_thread_count):

                def do_restart():
                    # Relaunch the app with the same command line
                    if getattr(sys, "frozen", False):
                        exe = sys.executable
                        args = sys.argv
                    else:
                        exe = sys.executable
                        # Reconstruct the command to use -m if run as a module
                        if sys.argv[0].endswith("__main__.py"):
                            args = [exe, "-m", "jira_manager"]
                        else:
                            args = [exe] + sys.argv
                    # On Windows, bring the new app window to the foreground
                    if sys.platform == "win32":
                        import ctypes

                        SW_SHOW = 5
                        # Start the new process
                        proc = subprocess.Popen(args, cwd=os.getcwd())
                        # Wait a moment for the window to appear
                        import time

                        time.sleep(0.5)
                        # Try to bring the new window to the foreground
                        ctypes.windll.user32.SetForegroundWindow(proc._handle)
                        ctypes.windll.user32.ShowWindow(proc._handle, SW_SHOW)
                    else:
                        subprocess.Popen(args, cwd=os.getcwd())
                    os._exit(0)

                root = self.panel_choice.get("root")
                popup = tk.Toplevel(root)
                popup.overrideredirect(1)
                # Center the popup over the root window
                w = 350
                h = 250
                x = root.winfo_rootx() + (root.winfo_width() // 2) - (w // 2)
                y = root.winfo_rooty() + (root.winfo_height() // 2) - (h // 2)
                popup.geometry(f"{w}x{h}+{x}+{y}")
                popup.transient(root)
                popup.grab_set()
                popup.lift()
                popup.focus_force()
                # Apply theme to popup
                self.theme_manager.register(popup, "frame")
                label = tk.Label(
                    popup,
                    text="CHANGE FROM SAFE MODE AT YOUR OWN RISK!\nThread count changed. Please restart the app for changes to take effect.",
                    wraplength=320,
                    font=("Trebuchet MS", 11),
                )
                label.pack(pady=20)
                self.theme_manager.register(label, "label")
                btn_frame = tk.Frame(popup)
                btn_frame.pack(pady=10)
                self.theme_manager.register(btn_frame, "frame")
                restart_btn = tk.Button(
                    btn_frame,
                    text="Restart Now",
                    command=do_restart,
                    font=("Trebuchet MS", 11, "bold"),
                )
                restart_btn.pack(side="left", padx=10)
                self.theme_manager.register(restart_btn, "flashy_button")
                later_btn = tk.Button(
                    btn_frame,
                    text="Later",
                    command=popup.destroy,
                    font=("Trebuchet MS", 11),
                )
                later_btn.pack(side="left", padx=10)
                self.theme_manager.register(later_btn, "base_button")
                return  # Don't update theme or switch panel until restart

            # NEED TO CALL UPDATE THEME HERE
            try:
                new_theme = payload["theme"]
                print(f"{new_theme=}")
                if new_theme.lower() == "light":
                    mode = self.light_mode
                elif new_theme.lower() == "dark":
                    mode = self.dark_mode
                else:
                    mode = "No mode registered"
                print(mode)
                theme_manager.update_theme(new_theme=mode)

                switch_panel(
                    "ticket_panel",
                    self.ui_state,
                    self.panel_choice,
                    self.widget_registry,
                    self.db_path,
                    self.theme_manager,
                    self.card_retainer,
                    self.selected_items,
                )

                ticket_cards = (
                    self.panel_choice["ticket_panel"]
                    .widget_registry.get("base_frame")
                    .winfo_children()
                )
                for card in ticket_cards:
                    if card.ticket_key in self.selected_items:
                        card.set_bg(self.theme_manager.theme["pending_color"])
                        card.widget_registry.get("select_btn").config(
                            text="Unselect",
                            bg=self.theme_manager.theme["pending_color"],
                        )

            except Exception as e:
                print(f"{e=}")
                pass

        def update_proxy_fields(event=None):
            proxy_panel.pack_forget()
            if proxy_option.get() == "Yes":
                proxy_panel.pack(fill="x", pady=5)
                self.theme_manager.register(proxy_panel, "frame")

        def update_auth_fields(event=None):
            basic_panel.pack_forget()
            token_panel.pack_forget()
            if selected_auth.get() == "Basic Auth":
                basic_panel.pack(fill="x", pady=5)
                self.theme_manager.register(basic_panel, "frame")
            else:
                token_panel.pack(fill="x", pady=5)
                self.theme_manager.register(token_panel, "frame")

        # DEFAULTS FOR COMBOBOX
        selected_auth = tk.StringVar(value=self.config.get("auth_type", "Basic Auth"))
        proxy_option = tk.StringVar(value=self.config.get("proxy_option", "No"))

        theme_option = tk.StringVar(
            value=self.config.get("theme", "Light")  # default to 'light' if not set
        )

        base_frame = tk.Frame(self)
        self.theme_manager.register(base_frame, "frame")

        form_frame = tk.Frame(base_frame)
        form_frame.pack(fill="both", expand=True)
        self.theme_manager.register(form_frame, "frame")

        footer_frame = tk.Frame(base_frame)
        footer_frame.pack(fill="x", side="bottom")
        self.theme_manager.register(footer_frame, "frame")

        selector_row = tk.Frame(form_frame)
        selector_row.pack(fill="x", pady=5)
        self.theme_manager.register(selector_row, "frame")

        # Row 0, Column 0 – Credential Type
        cred_label = tk.Label(
            selector_row,
            text="Credential Type:",
            font=self.font_style,
        )
        # cred_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        cred_label.grid(row=0, column=0, sticky="w", padx=(5, 10), pady=2)
        self.theme_manager.register(cred_label, "label")

        auth_type = ttk.Combobox(
            selector_row,
            textvariable=selected_auth,
            values=["Basic Auth", "Token Auth"],
            state="readonly",
            style="Custom.TCombobox",
        )
        # auth_type.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=2)
        auth_type.grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=2)
        self.theme_manager.register(auth_type, "combobox")

        # Row 0, Column 2 – Use Proxies
        proxy_label = tk.Label(
            selector_row,
            text="Use Proxies:",
            font=self.font_style,
        )
        # proxy_label.grid(row=0, column=2, sticky="w", padx=(0, 5), pady=2)
        proxy_label.grid(row=0, column=2, sticky="w", padx=(5, 10), pady=2)
        self.theme_manager.register(proxy_label, "label")

        proxy_type = ttk.Combobox(
            selector_row,
            textvariable=proxy_option,
            values=["No", "Yes"],
            state="readonly",
            style="Custom.TCombobox",
        )
        # proxy_type.grid(row=0, column=3, sticky="ew", pady=2)
        proxy_type.grid(row=0, column=3, sticky="ew", pady=2, padx=(5, 10))
        self.theme_manager.register(proxy_type, "combobox")

        # Row 1, Column 1 – Theme
        theme_label = tk.Label(
            selector_row,
            text="Theme:",
            font=self.font_style,
        )
        # theme_label.grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        theme_label.grid(row=1, column=0, sticky="w", padx=(5, 10), pady=2)
        self.theme_manager.register(theme_label, "label")

        theme = ttk.Combobox(
            selector_row,
            textvariable=theme_option,
            values=["Light", "Dark"],
            state="readonly",
            style="Custom.TCombobox",
        )
        # theme.grid(row=1, column=1, sticky="ew", pady=2)
        theme.grid(row=1, column=1, sticky="ew", pady=2, padx=(5, 10))
        self.theme_manager.register(theme, "combobox")

        # Thread Count Selector (Row 1, Column 2/3)
        thread_count_label = tk.Label(
            selector_row,
            text="Thread Count:",
            font=self.font_style,
        )
        # thread_count_label.grid(row=1, column=2, sticky="w", padx=(0, 5), pady=2)
        thread_count_label.grid(row=1, column=2, sticky="w", padx=(5, 10), pady=2)
        self.theme_manager.register(thread_count_label, "label")

        thread_count_values = ["Safe Mode", 8, 12, 16, 20, 24, 28, 32]
        display_to_value = {"Safe Mode": "safe_mode"}
        for v in thread_count_values[1:]:
            display_to_value[str(v)] = str(v)

        current_thread_count = self.config.get("thread_count", "safe_mode")
        if current_thread_count == "safe_mode":
            display_value = "Safe Mode"
        else:
            display_value = str(current_thread_count)
        thread_count_option = tk.StringVar(value=display_value)

        thread_count = ttk.Combobox(
            selector_row,
            textvariable=thread_count_option,
            values=[str(v) for v in thread_count_values],
            state="readonly",
            style="Custom.TCombobox",
        )
        # thread_count.grid(row=1, column=3, sticky="ew", pady=2)
        thread_count.grid(row=1, column=3, sticky="ew", pady=2, padx=(5, 10))
        self.theme_manager.register(thread_count, "combobox")

        # SEPERATOR IN FORM
        ttk.Separator(form_frame, orient="horizontal").pack(fill="x", pady=10)

        # Form Inputs
        jira_row = tk.Frame(form_frame)
        jira_row.pack(fill="x", pady=5)
        jira_row.columnconfigure(1, weight=1)
        self.theme_manager.register(jira_row, "frame")

        server_label = tk.Label(
            jira_row,
            text="Jira Server:",
            font=self.font_style,
        )
        server_label.pack(side="left", padx=(0, 5))
        self.theme_manager.register(server_label, "label")

        jira_server_input = EntryWithPlaceholder(
            jira_row,
            placeholder="Provide base url",
            font=self.font_style,
            initial_text=self.config.get("server", ""),
        )
        jira_server_input.pack(side="left", fill="x", expand=True, padx=10)
        self.theme_manager.register(jira_server_input, "placeholder_entry")
        proxy_panel = tk.Frame(form_frame)

        proxy_http = tk.Frame(proxy_panel)
        proxy_http.pack(fill="x", pady=5)
        proxy_http.columnconfigure(1, weight=1)
        self.theme_manager.register(proxy_http, "frame")
        http_label = tk.Label(
            proxy_http,
            text="HTTP Proxy:",
            font=self.font_style,
        )
        http_label.pack(side="left", padx=(0, 5))
        self.theme_manager.register(http_label, "label")
        http_input = tk.Entry(
            proxy_http,
        )
        http_input.pack(side="left", fill="x", expand=True, padx=10)
        http_input.insert(0, self.config.get("http_proxy", ""))
        self.theme_manager.register(http_input, "entry")
        proxy_https = tk.Frame(proxy_panel)
        proxy_https.pack(fill="x", pady=5)
        proxy_https.columnconfigure(1, weight=1)
        self.theme_manager.register(proxy_https, "frame")
        https_label = tk.Label(
            proxy_https,
            text="HTTPS Proxy:",
            font=self.font_style,
        )
        https_label.pack(side="left", padx=(0, 5))
        self.theme_manager.register(https_label, "label")
        https_input = tk.Entry(
            proxy_https,
        )
        https_input.pack(side="left", fill="x", expand=True, padx=10)
        https_input.insert(0, self.config.get("https_proxy", ""))
        self.theme_manager.register(https_input, "entry")
        basic_panel = tk.Frame(form_frame)

        user_row = tk.Frame(basic_panel)
        user_row.pack(fill="x", pady=5)
        user_row.columnconfigure(1, weight=1)
        self.theme_manager.register(user_row, "frame")
        user_label = tk.Label(
            user_row,
            text="User ID:",
            font=self.font_style,
        )
        user_label.pack(side="left", padx=(0, 5))
        self.theme_manager.register(user_label, "label")
        username_input = EntryWithPlaceholder(
            user_row,
            placeholder="Enter username or email",
            initial_text=self.config.get("username", ""),
        )
        username_input.pack(side="left", fill="x", expand=True, padx=10)
        self.theme_manager.register(username_input, "placeholder_entry")
        pass_row = tk.Frame(basic_panel)
        pass_row.pack(fill="x", pady=5)
        pass_row.columnconfigure(1, weight=1)
        self.theme_manager.register(pass_row, "frame")
        pass_label = tk.Label(
            pass_row,
            text="Password:",
            font=self.font_style,
        )
        pass_label.pack(side="left", padx=(0, 5))
        self.theme_manager.register(pass_label, "label")
        password_input = EntryWithPlaceholder(
            pass_row,
            placeholder="Enter password or token",
            initial_text=self.config.get("password", ""),
            show="*",
        )
        password_input.pack(side="left", fill="x", expand=True, padx=10)
        self.theme_manager.register(password_input, "placeholder_entry")
        token_panel = tk.Frame(form_frame)

        token_row = tk.Frame(token_panel)
        token_row.pack(fill="x", pady=5)
        token_row.columnconfigure(1, weight=1)
        self.theme_manager.register(token_row, "frame")
        token_label = tk.Label(
            token_row,
            text="Access Token:",
            font=self.font_style,
        )
        token_label.pack(side="left", padx=(0, 5))
        self.theme_manager.register(token_label, "label")
        token_input = EntryWithPlaceholder(
            token_row,
            placeholder="(Bearer Token) JWT or OAuth 2.0 only",
            show="*",
            initial_text=self.config.get("token", ""),
        )
        token_input.pack(side="left", fill="x", expand=True, padx=10)
        self.theme_manager.register(token_input, "placeholder_entry")
        proxy_type.bind("<<ComboboxSelected>>", update_proxy_fields)
        auth_type.bind("<<ComboboxSelected>>", update_auth_fields)

        update_proxy_fields()
        update_auth_fields()

        ttk.Separator(footer_frame, orient="horizontal").pack(fill="x", pady=10)
        save_button = tk.Button(
            footer_frame,
            text="Save",
            command=lambda: on_save(self.theme_manager),
        )
        save_button.pack(pady=(5, 10))
        self.theme_manager.register(save_button, "base_button")
        return base_frame


class ErrorMessageBuilder(tk.Frame):
    def __init__(self, master=None, theme_manager: ThemeManager = None):
        super().__init__(master)
        self.theme_manager = theme_manager
        self.message = "Do I See This?"

    def update_message(self, new_message: str):
        self.message = new_message

        # Only reuse if widget exists and is a compatible type
        if hasattr(self, "error_label") and self.error_label.winfo_exists():
            if isinstance(self.error_label, (tk.Label, tk.Message)):
                self.error_label.config(text=self.message)
            else:
                self.error_label.destroy()  # Clean out incompatible widget
                self.error_label = self.build_error_message()
                self.error_label.pack(fill="both", expand=True)
        else:
            self.error_label = self.build_error_message()
            self.error_label.pack(fill="both", expand=True)

    def build_error_message(self):
        border_frame = tk.Frame(self, padx=3, pady=3)
        self.theme_manager.register(border_frame, "error_border_frame")

        canvas = tk.Canvas(border_frame, width=550, height=125)
        canvas.pack(fill="both", expand=True)
        self.theme_manager.register(canvas, "error_canvas")

        scrollbar = tk.Scrollbar(border_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack_forget()

        content_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        self.theme_manager.register(content_frame, "frame")

        content_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )

        error_label = tk.Label(
            content_frame,
            text=f"⚠️ Error Occurred:\n\n{self.message}",
            wraplength=500,
            justify="left",
            padx=12,
            pady=12,
        )
        error_label.pack(fill="x")
        self.theme_manager.register(error_label, "error_label")

        # 🔽 Scroll to Top Button (bottom right corner)
        scroll_button = tk.Button(
            border_frame,
            text="↑",
            font=("Segoe UI", 12, "bold"),
            command=lambda: canvas.yview_moveto(0),
            width=2,
            height=1,
            bd=0,
            relief="flat",
            cursor="hand2",
        )
        scroll_button.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
        self.theme_manager.register(scroll_button, "base_button")

        return border_frame


class ErrorPopupBuilder(tk.Toplevel):
    def __init__(self, master=None, theme_manager=None, message="Do I See This?"):
        super().__init__(master)
        self.theme_manager = theme_manager
        self.message = message

        self.title("Error")
        self.resizable(False, False)
        self.transient(master)  # Keep popup on top of parent
        self.grab_set()  # Make it modal

        # 🧭 Center the popup on the screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        popup_width = 600
        popup_height = 300
        x = (screen_width // 2) - (popup_width // 2)
        y = (screen_height // 2) - (popup_height // 2)
        self.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        self.error_frame = self.build_error_message()
        self.error_frame.pack(fill="both", expand=True)

    def update_message(self, new_message: str):
        self.message = new_message

        if hasattr(self, "error_label") and self.error_label.winfo_exists():
            if isinstance(self.error_label, tk.Text):
                self.error_label.config(state="normal")
                self.error_label.delete("1.0", "end")
                self.error_label.insert(
                    "1.0", f"⚠️ Error Occurred:\n\n{self.message}", "margin"
                )
                self.error_label.config(state="disabled")
            else:
                self.error_label.destroy()
                self.error_frame = self.build_error_message()
                self.error_frame.pack(fill="both", expand=True)
        else:
            self.error_frame = self.build_error_message()
            self.error_frame.pack(fill="both", expand=True)

    def build_error_message(self):
        border_frame = tk.Frame(self, padx=3, pady=3)
        self.theme_manager.register(border_frame, "error_border_frame")

        canvas = tk.Canvas(border_frame, width=550, height=125)
        canvas.pack(fill="both", expand=True)
        self.theme_manager.register(canvas, "error_canvas")

        scrollbar = tk.Scrollbar(border_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack_forget()

        content_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        self.theme_manager.register(content_frame, "frame")

        content_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )

        # 📝 Replace Label with read-only Text widget
        self.error_label = tk.Text(
            content_frame,
            wrap="word",
            padx=12,
            pady=12,
            height=6,
            width=70,
            relief="flat",
            bg=self.cget("bg"),
            font=("Segoe UI", 10),
        )
        self.error_label.insert("1.0", f"⚠️ Error Occurred:\n\n{self.message}")
        self.error_label.config(state="disabled")  # Make it read-only
        self.error_label.pack(fill="x", expand=True)
        self.theme_manager.register(self.error_label, "error_label")

        scroll_button = tk.Button(
            border_frame,
            text="↑",
            font=("Segoe UI", 12, "bold"),
            command=lambda: canvas.yview_moveto(0),
            width=2,
            height=1,
            bd=0,
            relief="flat",
            cursor="hand2",
        )
        scroll_button.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
        self.theme_manager.register(scroll_button, "base_button")

        return border_frame


class TicketDisplayBuilder(tk.Frame):
    def __init__(
        self,
        master=None,
        theme_manager=None,
        db_path=None,
        selected_items=None,
        **kwargs,
    ):
        self.theme_manager = theme_manager
        self.db_path = db_path
        self.widget_registry = {}
        self.panel_choice = None
        self.selected_items = selected_items
        self.current_page = 1
        self.total_pages = None
        self.page_index = {}
        self.sql_query = "SELECT * FROM tickets"
        self.start_paging = SmartThread()
        self.end_paging = SmartThread()
        super().__init__(master, **kwargs)

        # # Build UI immediately or delay via external trigger
        # self.build()

    def load_page_index(self, db_path, sql, pull_type, lock, stop_flag=None):
        try:
            existed_count = 0
            total_pages = max(1, ceil(len(issues) / 50))
            if pull_type == "start":
                dynamic_sql = f"{sql} ORDER BY ticket_id DESC"
                pages = range(1, total_pages + 1)  # 1 to total_pages inclusive
            elif pull_type == "end":
                dynamic_sql = f"{sql} ORDER BY ticket_id ASC"
                pages = range(total_pages, 0, -1)  # total_pages down to 1 inclusive
            else:
                dynamic_sql = sql
            issues = run_sql_stmt(
                db_path,
                dynamic_sql,
                stmt_type="select",
            )
            if issues:
                for page in pages:
                    if stop_flag is not None and stop_flag.is_set():
                        print("Page index thread received stop signal, exiting early.")
                        break
                    start_idx = (page - 1) * 50
                    end_idx = start_idx + 50
                    page_issues = issues[start_idx:end_idx]
                    if not page_issues:
                        continue
                    with lock:
                        first_id = page_issues[0][0]
                        last_id = page_issues[-1][0]
                        if (
                            self.check_page_index(page) == False
                            and self.check_page_cursors(page, (first_id, last_id))
                            == False
                        ):
                            # self.update_first_ticket_id(first_id)
                            # self.update_last_ticket_id(last_id)
                            self.update_page_index(page, (first_id, last_id))
                            print(f"Loaded page {page} index: {first_id} to {last_id}")
                            if existed_count > 0:
                                existed_count -= 1
                        else:
                            existed_count += 1
                        if existed_count >= 5:
                            break
            print(f"{self.page_index=}\nPage index thread finished normally.")
        except Exception as e:
            import traceback

            print("Exception in load_page_index:", e)
            traceback.print_exc()

    def check_page_index(self, page):
        if page in self.page_index.keys():
            return True
        return False

    def update_page_index(self, page, items):
        if page not in self.page_index.keys():
            self.page_index[page] = items

    def check_page_cursors(self, page, cursors):
        if page in self.page_index.keys():
            if self.page_index[page] == cursors:
                return True
        return False

    def update_page_number(self, new_page_number):
        self.current_page = new_page_number

    def update_total_pages(self, new_total_pages):
        self.total_pages = new_total_pages

    def set_panel_choice(self, panel_choice):
        self.panel_choice = panel_choice
        # Always re-bind mousewheel when ticket panel is shown
        canvas = self.widget_registry.get("canvas")
        if canvas:

            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            canvas.bind("<MouseWheel>", _on_mousewheel)

    def update_ticket_bucket_with_single(
        self, ticket, panel_choice, theme_manager, selected_items, card_retainer=None
    ):
        # print(f"{panel_choice=}")  # Debug print commented out
        # base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")
        base_frame = self.widget_registry.get("base_frame")
        card = TicketCard(
            ticket,
            theme_manager,
            master=base_frame,
            selected_items=selected_items,
            card_retainer=card_retainer,
        )
        # print(f"{ticket=} from update_ticket_bucket_with_single")
        card.update_panel_choice(panel_choice=panel_choice)
        if ticket["key"] in selected_items:
            card.set_bg(theme_manager.theme["pending_color"])
            card.widget_registry.get("select_btn").config(
                text="Unselect", bg=theme_manager.theme["pending_color"]
            )
        # Always pack at the bottom for correct order
        card.pack(side="top", fill="x", padx=5, pady=3, expand=True)

    def update_ticket_bucket(
        self,
        ticket_bucket_items,
        panel_choice,
        theme_manager,
        selected_items,
        card_retainer=None,
    ):
        # base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")
        base_frame = self.widget_registry.get("base_frame")

        # Remove all existing ticket widgets from the base_frame
        for child in base_frame.winfo_children():
            child.destroy()

        max_cols = 5
        # print(f"{ticket_bucket_items=}")
        # Make columns expandable
        for col in range(max_cols):
            base_frame.columnconfigure(col, weight=1)
        for index, item in enumerate(ticket_bucket_items):
            row = index // max_cols
            col = index % max_cols
            self.update_ticket_bucket_with_single(
                item,
                panel_choice,
                theme_manager,
                selected_items,
                card_retainer=card_retainer,
            )

    def set_page_contents(
        self,
        pg_num: int,
        selected_items,
        db_path,
        sql,
        base_frame,
        params=None,
        pre_fetched_issues=None,
    ):
        last_page = self.total_pages
        print(f"{pg_num=}")
        # print(f"New Start = {self.last_ticket_id}")
        if pre_fetched_issues is not None:
            issues = pre_fetched_issues
        else:
            issues = run_sql_stmt(
                db_path,
                sql,
                stmt_type="select",
                params=params,
            )
        for issue in issues:
            print(f"ticket_id={issue[0]}, key={issue[1]}")
        if issues:
            last_id = issues[-1][0]
            first_id = issues[0][0]
            if self.check_page_index(pg_num) == False:
                # self.update_last_ticket_id(last_id)
                # self.update_first_ticket_id(first_id)
                print(f"{first_id=}, {last_id=}")
                # Always update the page index for this page after a jump or navigation
                self.update_page_index(pg_num, (first_id, last_id))
        else:
            # Handle empty page (disable prev/next, show message, etc.)
            print("No tickets found for this page.")
            return

        # Convert DB rows to ticket dicts as needed by your UI
        # Adjust this as needed for your TicketCard
        tickets_to_show = []
        for issue in issues:
            # Example: id at index 0, key at index 1
            ticket = {"id": issue[0], "key": issue[1]}
            tickets_to_show.append(ticket)
        print(f"{tickets_to_show=}")

        # Update page indicator and total page count
        if "current_pg" in self.widget_registry:
            self.widget_registry["current_pg"].config(text=str(pg_num))
        if "total_tickets" in self.widget_registry:
            self.widget_registry["total_tickets"].config(text=str(last_page))

        # If there are no tickets to show, remove Return to Top button and frame
        if not tickets_to_show:
            # base_frame = self.widget_registry.get("base_frame")
            if base_frame:
                # Remove button and frame
                if hasattr(self, "return_top_btn") and self.return_top_btn:
                    try:
                        self.return_top_btn.destroy()
                    except Exception:
                        pass
                    self.return_top_btn = None
                for child in base_frame.winfo_children():
                    if isinstance(child, tk.Frame) and getattr(
                        child, "_is_return_top_btn_frame", False
                    ):
                        child.destroy()

        # base_frame = self.panel_choice["ticket_panel"].widget_registry.get("base_frame")
        parent = base_frame.master
        overlay = tk.Frame(parent)
        overlay.place(
            x=base_frame.winfo_x(),
            y=base_frame.winfo_y(),
            width=base_frame.winfo_width(),
            height=base_frame.winfo_height(),
        )
        self.theme_manager.register(overlay, "frame")
        overlay.lift()
        parent.update_idletasks()
        for child in base_frame.winfo_children():
            # Do not destroy the loadbar_frame (and its children)
            if getattr(child, "is_loadbar_frame", False):
                continue
            child.destroy()
        self.update_ticket_bucket(
            tickets_to_show,
            self.panel_choice,
            self.theme_manager,
            self.selected_items,
            card_retainer=None,
        )

        # Initial call after building ticket board
        self.update_return_top_btn()

        base_frame.update_idletasks()
        overlay.place(
            x=base_frame.winfo_x(),
            y=base_frame.winfo_y(),
            width=base_frame.winfo_width(),
            height=base_frame.winfo_height(),
        )
        overlay.lift()

        def remove_overlay():
            overlay.destroy()

        parent.after(120, remove_overlay)
        self.update_return_top_btn()

    def scroll_to_top(self):
        canvas = self.widget_registry.get("canvas")
        canvas.yview_moveto(0)

    def update_return_top_btn(self):
        """ WILL NEED TO FIX THIS LATER DATE """
        pass
        # Get current page and ticket range
        # tickets_per_page = 50
        # total_tickets = len(self.tickets) if self.tickets else 0
        # pg_num = 1
        # if "current_pg" in self.widget_registry:
        #     try:
        #         pg_num = int(self.widget_registry["current_pg"].cget("text"))
        #     except Exception:
        #         pg_num = 1
        # minimum = (pg_num - 1) * tickets_per_page
        # maximum = min(pg_num * tickets_per_page, total_tickets)
        # ticket_count = maximum - minimum
        # base_frame = self.widget_registry.get("base_frame")
        # if not base_frame:
        #     return
        # # Remove any previous button and frame
        # if hasattr(self, "return_top_btn") and self.return_top_btn:
        #     try:
        #         self.return_top_btn.destroy()
        #     except Exception:
        #         pass
        #     self.return_top_btn = None
        # # Remove any previous button frame (if you store a reference, e.g. self.return_top_btn_frame)
        # for child in base_frame.winfo_children():
        #     if isinstance(child, tk.Frame) and getattr(
        #         child, "_is_return_top_btn_frame", False
        #     ):
        #         child.destroy()
        # # Show 'Return to Top' only if the vertical scrollbar is visible (content overflows) and ticket count >= 25
        # canvas = self.widget_registry.get("canvas")
        # base_frame.update_idletasks()
        # needs_scroll = False
        # if canvas is not None:
        #     scrollregion = canvas.bbox("all")
        #     if scrollregion:
        #         visible_height = canvas.winfo_height()
        #         content_height = scrollregion[3] - scrollregion[1]
        #         needs_scroll = content_height > visible_height
        # if needs_scroll and ticket_count >= 25:
        #     btn_frame = tk.Frame(base_frame)
        #     btn_frame._is_return_top_btn_frame = True  # Mark for future cleanup
        #     btn_frame.pack(side="top", fill="x", pady=10)
        #     self.theme_manager.register(btn_frame, "frame")
        #     self.return_top_btn = tk.Button(
        #         btn_frame,
        #         text="Return to Top",
        #         command=self.scroll_to_top,
        #         font=("Segoe UI", 12, "bold"),
        #         cursor="hand2",
        #     )
        #     self.return_top_btn.pack(side="top", pady=5)
        #     self.theme_manager.register(self.return_top_btn, "base_button")

    def update_nav_buttons(self, page_num):
        # Call this after every page change
        last_page = self.total_pages
        prev_btn = self.widget_registry.get("prev_btn")
        nxt_btn = self.widget_registry.get("nxt_btn")
        if page_num <= 1:
            prev_btn.config(state="disabled")
        else:
            prev_btn.config(state="normal")
        if page_num >= last_page:
            nxt_btn.config(state="disabled")
        else:
            nxt_btn.config(state="normal")

    def prev_action(self):
        prev_btn = self.widget_registry.get("prev_btn")
        nxt_btn = self.widget_registry.get("nxt_btn")
        if prev_btn:
            prev_btn.config(state="disabled")
        if nxt_btn:
            nxt_btn.config(state="disabled")
        current_page = self.current_page
        db_path = self.panel_choice.get("db_path")
        new_pg = max(1, current_page - 1)
        first_id, _ = self.page_index.get(new_pg)
        if current_page == 1:
            sql = "SELECT * FROM tickets ORDER BY ticket_id DESC LIMIT 50;"
            self.set_page_contents(
                1,
                self.selected_items,
                db_path,
                sql,
                self.widget_registry.get("base_frame"),
            )
        else:
            # Strict keyset paging: use first_id as cursor, ASC, then reverse
            # first_id = self.first_ticket_id
            sql = "SELECT * FROM tickets WHERE ticket_id > ? ORDER BY ticket_id ASC LIMIT 50;"
            issues = run_sql_stmt(db_path, sql, stmt_type="select", params=(first_id,))
            issues = list(reversed(issues))
            self.set_page_contents(
                new_pg, self.selected_items, db_path, None, None, issues
            )
        self.update_page_number(new_pg)

        def enable_buttons():
            self.update_nav_buttons(new_pg)

        if prev_btn:
            prev_btn.after(150, enable_buttons)
        self.scroll_to_top()

    def nxt_action(self):
        prev_btn = self.widget_registry.get("prev_btn")
        nxt_btn = self.widget_registry.get("nxt_btn")
        if prev_btn:
            prev_btn.config(state="disabled")
        if nxt_btn:
            nxt_btn.config(state="disabled")
        current_page = self.current_page
        last_page = self.total_pages
        db_path = self.panel_choice.get("db_path")
        new_pg = min(last_page, current_page + 1)
        _, last_id = self.page_index.get(new_pg)
        # Strict keyset paging: use last_id as cursor, DESC
        # last_id = self.last_ticket_id
        sql = "SELECT * FROM tickets WHERE ticket_id < ? ORDER BY ticket_id DESC LIMIT 50;"
        self.set_page_contents(
            new_pg,
            self.selected_items,
            db_path,
            sql,
            self.widget_registry.get("base_frame"),
            (last_id,),
        )
        self.update_page_number(new_pg)

        def enable_buttons():
            self.update_nav_buttons(new_pg)

        if nxt_btn:
            nxt_btn.after(150, enable_buttons)
        self.scroll_to_top()

    def poll_page_index_threads(self):
        if self.start_paging.is_alive() or self.end_paging.is_alive():
            self.after(100, self.poll_page_index_threads)
        else:
            print("Page index threads finished.")

    def build(self):

        """ BUILD PAGE INDEX THEN DISPLAY CURRENT PAGE"""

        # max_pg_count = ceil(len((self.tickets)) / 50)
        tool_bar = tk.Frame(self)
        tool_bar.pack(fill="x", padx=10, pady=10)
        self.widget_registry["tool_bar"] = tool_bar
        self.theme_manager.register(tool_bar, "frame")

        prev_btn = tk.Button(tool_bar, text="←", command=self.prev_action)
        prev_btn.pack(side="left", padx=10, pady=10)
        prev_btn.config(state="disabled")
        self.theme_manager.register(prev_btn, "base_button")
        self.widget_registry["prev_btn"] = prev_btn

        current_pg = tk.Label(tool_bar, text="1", font=("Trebuchet MS", 12))
        current_pg.pack(side="left")
        self.theme_manager.register(current_pg, "flashy_label")
        self.widget_registry["current_pg"] = current_pg

        slash = tk.Label(tool_bar, text="/", font=("Trebuchet MS", 14, "bold"))
        slash.pack(side="left")
        self.theme_manager.register(slash, "label")

        total = tk.Label(
            tool_bar, text=f"{self.total_pages}", font=("Trebuchet MS", 14, "bold")
        )
        total.pack(side="left")
        self.theme_manager.register(total, "label")
        self.widget_registry["total_tickets"] = total

        nxt_btn = tk.Button(tool_bar, text="→", command=self.nxt_action)
        nxt_btn.pack(side="left", padx=10, pady=10)
        self.theme_manager.register(nxt_btn, "base_button")
        self.widget_registry["nxt_btn"] = nxt_btn

        # Dropdown-style page jump
        from jira_manager.custom_widgets import EntryWithPlaceholder

        page_jump_frame = tk.Frame(tool_bar)
        self.theme_manager.register(page_jump_frame, "frame")
        page_jump_frame.pack_forget()  # Hidden by default

        page_jump_entry = EntryWithPlaceholder(
            page_jump_frame,
            placeholder="page",
            font=("Trebuchet MS", 12),
            initial_text="",
            width=7,
        )
        page_jump_entry.pack(side="left", padx=(5, 5))
        self.theme_manager.register(page_jump_entry, "placeholder_entry")

        # Bind Enter key to trigger page jump
        # Bind Enter key to trigger page jump with correct arguments
        def handle_page_jump_event(event=None):
            try:
                value = page_jump_entry.get()
                page = int(value)
                jump_to_page(self, page)
                page_jump_entry.reset_to_placeholder()
                # Move focus away so placeholder appears as hint
                self.focus_set()
            except Exception:
                page_jump_entry.reset_to_placeholder()
                self.focus_set()

        page_jump_entry.bind("<Return>", handle_page_jump_event)

        def jump_to_page(self, page):
            last_page = self.total_pages
            db_path = self.panel_choice.get("db_path")
            page = max(1, min(page, last_page))
            if page == 1:
                sql = "SELECT * FROM tickets ORDER BY ticket_id DESC LIMIT 50;"
                self.set_page_contents(page, self.selected_items, db_path, sql)
            elif (page - 1) in self.page_index:
                _, prev_last_id = self.page_index[page - 1]
                sql = "SELECT * FROM tickets WHERE ticket_id < ? ORDER BY ticket_id DESC LIMIT 50;"
                self.set_page_contents(
                    page, self.selected_items, db_path, sql, (prev_last_id,)
                )
            else:
                show_internal = self.widget_registry.get("show_internal_loadbar")
                hide_internal = self.widget_registry.get("hide_internal_loadbar")
                if show_internal:
                    show_internal()
                    internal_loadbar = self.widget_registry.get("internal_loadbar")
                    internal_loadbar_label = self.widget_registry.get(
                        "internal_loadbar_label"
                    )
                    if internal_loadbar:
                        internal_loadbar.config(mode="determinate")
                        internal_loadbar["value"] = 100
                    if internal_loadbar_label:
                        internal_loadbar_label.config(text="1/1")
                offset = (page - 1) * 50
                sql = f"SELECT * FROM tickets ORDER BY ticket_id DESC LIMIT 50 OFFSET {offset};"
                self.set_page_contents(page, self.selected_items, db_path, sql)
                if hide_internal:
                    self.after(200, hide_internal)
            self.update_page_number(page)
            self.update_nav_buttons(page)
            self.widget_registry["current_pg"].config(text=str(page))
            self.scroll_to_top()

        go_btn = tk.Button(
            page_jump_frame,
            text="Go",
            command=handle_page_jump_event,
            font=("Segoe UI", 11),
            cursor="hand2",
        )
        go_btn.pack(side="left", padx=(0, 5))
        self.theme_manager.register(go_btn, "base_button")

        def toggle_page_jump():
            if page_jump_frame.winfo_ismapped():
                page_jump_frame.pack_forget()
            else:
                page_jump_frame.pack(side="left", padx=(5, 10))
                page_jump_entry.reset_to_placeholder()

        dropdown_btn = tk.Button(
            tool_bar,
            text="\u25b6",
            command=toggle_page_jump,
            font=("Segoe UI", 13),
            cursor="hand2",
            width=2,
        )
        dropdown_btn.pack(side="left", padx=(20, 0))
        self.theme_manager.register(dropdown_btn, "base_button")

        canvas = tk.Canvas(self)
        canvas.pack(fill="both", expand=True, side="left")
        self.theme_manager.register(canvas, "frame")
        # Always show the scrollbar for reliable scrolling
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        self.widget_registry["canvas"] = canvas

        # Simple, direct mouse wheel binding
        def on_mousewheel(event):
            print(
                f"[DEBUG] on_mousewheel: canvas={canvas}, has focus={canvas == canvas.focus_displayof()}"
            )
            if canvas != canvas.focus_displayof():
                canvas.focus_set()
                print(f"[DEBUG] Focus set to canvas: {canvas}")
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")
            return "break"

        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel)
        canvas.bind("<Button-5>", on_mousewheel)

        base_frame = tk.Frame(canvas)
        self.widget_registry["base_frame"] = base_frame
        self.theme_manager.register(base_frame, "frame")

        # Add loadbar_frame to the right side of base_frame (only if not already present)
        if "loadbar_frame" not in self.widget_registry:
            loadbar_frame = tk.Frame(tool_bar)
            loadbar_frame.is_loadbar_frame = True  # Mark for persistence
            loadbar_frame.pack(side="right", fill="y", padx=(10, 0), pady=10)
            self.widget_registry["loadbar_frame"] = loadbar_frame
            self.theme_manager.register(loadbar_frame, "frame")
            # Add two horizontal progress bars
            # External loadbar with label to the right
            external_loadbar_frame = tk.Frame(loadbar_frame)
            external_loadbar_frame.pack(pady=(10, 5), padx=10, fill="x")
            external_loadbar = ttk.Progressbar(
                external_loadbar_frame,
                orient="horizontal",
                length=120,
                mode="determinate",
                maximum=100,
            )
            external_loadbar.pack(side="left", fill="y", expand=True)
            external_loadbar_label = tk.Label(
                external_loadbar_frame,
                text="1/2",
                font=("Segoe UI", 9, "bold"),
                anchor="center",
            )
            external_loadbar_label.pack(side="left", padx=(0, 0), fill="y")
            # Internal loadbar with overlay label for queue progress
            internal_loadbar_frame = tk.Frame(loadbar_frame)
            # Do NOT pack internal_loadbar_frame yet (hidden by default)
            internal_loadbar = ttk.Progressbar(
                internal_loadbar_frame,
                orient="horizontal",
                length=120,
                mode="determinate",
                maximum=100,
            )
            internal_loadbar.pack(side="left", fill="y", expand=True)
            internal_loadbar_label = tk.Label(
                internal_loadbar_frame,
                text="",
                font=("Segoe UI", 9, "bold"),
                anchor="center",
            )
            internal_loadbar_label.pack(side="left", padx=(0, 0), fill="y")
            # Register in widget_registry for access elsewhere
            self.widget_registry["external_loadbar"] = external_loadbar
            self.widget_registry["external_loadbar_label"] = external_loadbar_label
            self.widget_registry["internal_loadbar"] = internal_loadbar
            self.widget_registry["internal_loadbar_label"] = internal_loadbar_label
            self.widget_registry["internal_loadbar_frame"] = internal_loadbar_frame
            # Register with theme_manager for dynamic theming
            self.theme_manager.register(external_loadbar, "loadbar")
            self.theme_manager.register(external_loadbar_label, "loadbar_label")
            self.theme_manager.register(internal_loadbar, "loadbar")
            self.theme_manager.register(internal_loadbar_label, "loadbar_label")

        # Helper methods to show/hide the internal loadbar
        def show_internal_loadbar():
            frame = self.widget_registry.get("internal_loadbar_frame")
            if frame and not frame.winfo_ismapped():
                frame.pack(pady=(5, 10), padx=10, fill="x")

        def hide_internal_loadbar():
            frame = self.widget_registry.get("internal_loadbar_frame")
            if frame and frame.winfo_ismapped():
                frame.pack_forget()

        self.widget_registry["show_internal_loadbar"] = show_internal_loadbar
        self.widget_registry["hide_internal_loadbar"] = hide_internal_loadbar

        window_id = canvas.create_window((0, 0), window=base_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        base_frame.bind("<Configure>", on_configure)

        def on_resize(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", on_resize)

        # Optional: Scroll with mousewheel (for intuitive UX even without visible scrollbar)
        def _on_mousewheel(event):
            print(
                f"[DEBUG] _on_mousewheel: canvas={canvas}, has focus={canvas.focus_displayof()}"
            )
            if canvas != canvas.focus_displayof():
                canvas.focus_set()
                print(f"[DEBUG] Focus set to canvas: {canvas}")
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)


        """ NEED TO FINISH THIS PART / WILL BE FOR LOADING PAGE INDEX AND LOADBAR POPUP DISPLAY / HANDLING """
        if self.start_paging.is_alive() or self.end_paging.is_alive():
            self.after(100, self.poll_page_index_threads)

        # Initial population of tickets
        self.set_page_contents(
            self.current_page,
            self.selected_items,
            self.db_path,
            self.sql_query,
            self.widget_registry.get("base_frame"),
        )
