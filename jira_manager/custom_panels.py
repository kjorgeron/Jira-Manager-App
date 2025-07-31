import platform
import tkinter as tk
from tkinter import ttk
from jira_manager.themes import ThemeManager
from jira_manager.file_manager import load_data, save_data
from jira_manager.custom_widgets import EntryWithPlaceholder, TicketCard
from jira_manager.sql_manager import run_sql_stmt
from threading import Thread
from math import ceil
from time import sleep


def batch_list(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]


def update_ticket_bucket_with_single(ticket, panel_choice, theme_manager):
    base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")

    card = TicketCard(ticket, theme_manager, master=base_frame)
    children = base_frame.winfo_children()
    if children and children[0].winfo_ismapped():
        card.pack(side="top", fill="x", padx=5, pady=3, before=children[0])
    else:
        card.pack(side="top", fill="x", padx=5, pady=3)


def update_ticket_bucket(ticket_bucket_items, panel_choice, theme_manager):
    base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")
    max_cols = 5

    # Make columns expandable
    for col in range(max_cols):
        base_frame.columnconfigure(col, weight=1)
    for index, item in enumerate(ticket_bucket_items):
        row = index // max_cols
        col = index % max_cols
        update_ticket_bucket_with_single(item, panel_choice, theme_manager)


def switch_panel(
    panel_key,
    ui_state,
    panel_choice,
    widget_registry,
    db_path: str = None,
    theme_manager: ThemeManager = None,
    card_retainer: list = None,
    thread_count: int = None,
):
    print(f"PANEL SWITCH -> {panel_key}")
    current = ui_state.get("active_panel")
    if current:
        current.pack_forget()
    next_panel = panel_choice[panel_key]
    if panel_key == "error_panel":
        widget_registry.get("welcome_label").pack_forget()
        next_panel.pack(fill="x", padx=100, pady=10)
    if panel_key == "configure_panel":
        widget_registry.get("welcome_label").pack_forget()
        next_panel.pack(fill="both", expand=True, padx=10, pady=10)
    if panel_key == "ticket_panel":
        if db_path:
            try:
                issues = run_sql_stmt(
                    db_path,
                    "SELECT * FROM tickets ORDER BY CAST(SUBSTR(key, INSTR(key, '-') + 1) AS INTEGER) DESC;",
                    stmt_type="select",
                )
                show_issues = []
                for i, issue in enumerate(issues):
                    show = {"key": issue[1]}
                    if show not in panel_choice["ticket_panel"].tickets:
                        panel_choice["ticket_panel"].tickets.append(show)

                    if i < 50:
                        show_issues.append(show)
                print(f"{len(show_issues)=}")
                print(f"{len(card_retainer)=}")
                panel_choice["ticket_panel"].widget_registry.get(
                    "total_tickets"
                ).config(text=f"{ceil(len(panel_choice["ticket_panel"].tickets) / 50)}")
                update_ticket_bucket(show_issues, panel_choice, theme_manager)

            except:
                # NEED TO ADD ERROR HANDLING
                pass
        widget = widget_registry.get("welcome_label")
        widget.config(text="Ticket Bucket")
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
        highlightthickness=0,
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
            highlightthickness=highlightthickness,
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

    def build_form(self):

        # INTERNAL FUNCTIONS
        def get_clean_value(widget):
            value = widget.get()
            if value != widget.placeholder or widget["fg"] != widget.placeholder_color:
                return value
            return ""

        def on_save(
            theme_manager: ThemeManager,
        ):  # THIS ROOT PASS NEEDS TO BE REMOVED / UPDATE FUNC TO FIT NEW CLASS IN THEMES.PY
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

            # SAVE PAYLOAD DATA
            save_data(payload)

            # NEED TO CALL UPDATE THEME HERE
            """ERROR FROM HERE... TAKES AWHILE OF TOOL USE TO SEE SMALL UI ERROR"""
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
        cred_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        self.theme_manager.register(cred_label, "label")

        auth_type = ttk.Combobox(
            selector_row,
            textvariable=selected_auth,
            values=["Basic Auth", "Token Auth"],
            state="readonly",
            style="Custom.TCombobox",
        )
        auth_type.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=2)
        self.theme_manager.register(auth_type, "combobox")

        # Row 0, Column 2 – Use Proxies
        proxy_label = tk.Label(
            selector_row,
            text="Use Proxies:",
            font=self.font_style,
        )
        proxy_label.grid(row=0, column=2, sticky="w", padx=(0, 5), pady=2)
        self.theme_manager.register(proxy_label, "label")

        proxy_type = ttk.Combobox(
            selector_row,
            textvariable=proxy_option,
            values=["No", "Yes"],
            state="readonly",
            style="Custom.TCombobox",
        )
        proxy_type.grid(row=0, column=3, sticky="ew", pady=2)
        self.theme_manager.register(proxy_type, "combobox")

        # Row 1, Column 1 – Theme
        theme_label = tk.Label(
            selector_row,
            text="Theme:",
            font=self.font_style,
        )
        theme_label.grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        self.theme_manager.register(theme_label, "label")

        theme = ttk.Combobox(
            selector_row,
            textvariable=theme_option,
            values=["Light", "Dark"],
            state="readonly",
            style="Custom.TCombobox",
        )
        theme.grid(row=1, column=1, sticky="ew", pady=2)
        self.theme_manager.register(theme, "combobox")

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
        canvas.bind_all(
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


class TicketDisplayBuilder(tk.Frame):
    def __init__(self, master=None, theme_manager=None, tickets=None, **kwargs):
        super().__init__(master, **kwargs)
        self.theme_manager = theme_manager
        self.widget_registry = {}
        self.tickets = tickets
        self.panel_choice = None

        # Build UI immediately or delay via external trigger
        self._build_ticket_board()

    def set_panel_choice(self, panel_choice):
        self.panel_choice = panel_choice

    def set_page_contents(self, pg_num: int):
        maximum = pg_num * 50
        minimum = maximum - 50

        if maximum > len(self.tickets):
            maximum = len(self.tickets)

        base_frame = self.panel_choice["ticket_panel"].widget_registry.get("base_frame")
        children = base_frame.winfo_children()
        for child in children:
            child.destroy()

        update_ticket_bucket(
            self.tickets[minimum:maximum], self.panel_choice, self.theme_manager
        )
        print(f"{minimum=}\n{maximum=}")

    # def prev_action(self):
    #     pg_num = self.widget_registry.get("current_pg")
    #     self.widget_registry.get("prev_btn").config(state="disabled")

    #     if int(pg_num.cget("text")) > 1:
    #         new_pg = int(pg_num.cget("text")) - 1
    #     else:
    #         new_pg = 1

    #     self.set_page_contents(new_pg)
    #     pg_num.config(text=f"{new_pg}")

    #     # Schedule re-enable after 100ms
    #     self.widget_registry.get("prev_btn").after(100, lambda: self.widget_registry.get("prev_btn").config(state="normal"))

    # def nxt_action(self):
    #     pg_num = self.widget_registry.get("current_pg")
    #     self.widget_registry.get("nxt_btn").config(state="disabled")

    #     if int(pg_num.cget("text")) + 1 <= ceil(len(self.tickets) / 50):
    #         new_pg = int(pg_num.cget("text")) + 1
    #     else:
    #         new_pg = ceil(len(self.tickets) / 50)

    #     self.set_page_contents(new_pg)
    #     pg_num.config(text=f"{new_pg}")

    #     # Re-enable after 100ms non-blocking
    #     self.widget_registry.get("nxt_btn").after(100, lambda: self.widget_registry.get("nxt_btn").config(state="normal"))

    def prev_action(self):
        pg_num = self.widget_registry.get("current_pg")
        self.widget_registry.get("prev_btn").config(state="disabled")
        self.widget_registry.get("nxt_btn").config(state="disabled")  # Pre-disable next_btn

        current_page = int(pg_num.cget("text"))
        new_pg = current_page - 1 if current_page > 1 else 1

        self.set_page_contents(new_pg)
        pg_num.config(text=f"{new_pg}")

        def enable_buttons():
            # Enable or disable based on new page value
            if new_pg > 1:
                self.widget_registry.get("prev_btn").config(state="normal")
            if new_pg < ceil(len(self.tickets) / 50):
                self.widget_registry.get("nxt_btn").config(state="normal")

        self.widget_registry.get("prev_btn").after(100, enable_buttons)

    def nxt_action(self):
        pg_num = self.widget_registry.get("current_pg")
        self.widget_registry.get("nxt_btn").config(state="disabled")
        self.widget_registry.get("prev_btn").config(state="disabled")  # Pre-disable prev_btn

        current_page = int(pg_num.cget("text"))
        last_page = ceil(len(self.tickets) / 50)
        new_pg = current_page + 1 if current_page < last_page else last_page

        self.set_page_contents(new_pg)
        pg_num.config(text=f"{new_pg}")

        def enable_buttons():
            # Enable or disable based on new page value
            if new_pg > 1:
                self.widget_registry.get("prev_btn").config(state="normal")
            if new_pg < last_page:
                self.widget_registry.get("nxt_btn").config(state="normal")

        self.widget_registry.get("nxt_btn").after(100, enable_buttons)

    def _build_ticket_board(self):
        max_pg_count = ceil(len((self.tickets)) / 50)
        tool_bar = tk.Frame(self)
        tool_bar.pack(fill="x", padx=10, pady=10)
        self.theme_manager.register(tool_bar, "frame")

        prev_btn = tk.Button(tool_bar, text="←", command=self.prev_action)
        prev_btn.pack(side="left", padx=10, pady=10)
        prev_btn.config(state="disabled")
        self.theme_manager.register(prev_btn, "base_button")
        self.widget_registry["prev_btn"] = prev_btn

        current_pg = tk.Label(tool_bar, text="1", font=("Trebuchet MS", 12), width=max_pg_count + 1)
        current_pg.pack(side="left")
        self.theme_manager.register(current_pg, "flashy_label")
        self.widget_registry["current_pg"] = current_pg

        slash = tk.Label(tool_bar, text="/", font=("Trebuchet MS", 14, "bold"))
        slash.pack(side="left")
        self.theme_manager.register(slash, "label")

        total = tk.Label(
            tool_bar, text=f"{len(self.tickets)}", font=("Trebuchet MS", 14, "bold")
        )
        total.pack(side="left")
        self.theme_manager.register(total, "label")
        self.widget_registry["total_tickets"] = total

        nxt_btn = tk.Button(tool_bar, text="→", command=self.nxt_action)
        nxt_btn.pack(side="left", padx=10, pady=10)
        self.theme_manager.register(nxt_btn, "base_button")
        self.widget_registry["nxt_btn"] = nxt_btn

        canvas = tk.Canvas(self, highlightthickness=0)
        canvas.pack(fill="both", expand=True, side="left")
        self.theme_manager.register(canvas, "frame")
        # Scrollbar is created but not packed, so it's hidden
        hidden_scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=hidden_scrollbar.set)

        base_frame = tk.Frame(canvas)
        self.widget_registry["base_frame"] = base_frame
        self.theme_manager.register(base_frame, "frame")

        window_id = canvas.create_window((0, 0), window=base_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        base_frame.bind("<Configure>", on_configure)

        def on_resize(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", on_resize)

        # Optional: Scroll with mousewheel (for intuitive UX even without visible scrollbar)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)


class TicketFormUI(tk.Frame):
    def __init__(self, master, field_layout):
        super().__init__(master)
        self.field_layout = field_layout
        self.entries = {}
        self.build_ui()

    def build_ui(self):
        row = 0
        for field in self.field_layout:
            label = ttk.Label(self, text=field["name"])
            label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

            widget_type = field["widget"]
            default = field["value"]

            # Assign widget based on type
            if widget_type == "TextEntry":
                entry = ttk.Entry(self)
                entry.insert(0, default)
            elif widget_type == "RichTextBox":
                entry = tk.Text(self, height=4, width=40)
                entry.insert("1.0", default)
            elif widget_type == "Dropdown":
                values = [
                    v["name"] if isinstance(v, dict) else v
                    for v in field.get("allowed", [])
                ]
                entry = ttk.Combobox(self, values=values)
                if default:
                    entry.set(
                        default
                        if isinstance(default, str)
                        else getattr(default, "name", "")
                    )
            elif widget_type == "MultiSelect":
                entry = tk.Listbox(self, selectmode=tk.MULTIPLE)
                for v in field.get("allowed", []):
                    entry.insert(tk.END, v["name"] if isinstance(v, dict) else v)
            elif widget_type == "UserPicker":
                entry = ttk.Combobox(self, values=["Kevin", "User A", "User B"])
                if default:
                    entry.set(default)
            elif widget_type == "DatePicker":
                entry = ttk.Entry(self)
                entry.insert(0, default or "YYYY-MM-DD")
            elif widget_type == "NumericEntry":
                entry = ttk.Entry(self)
                entry.insert(0, str(default) if default else "0")
            else:
                entry = ttk.Entry(self)
                entry.insert(0, str(default) if default else "")

            entry.grid(row=row, column=1, padx=5, pady=5)
            self.entries[field["id"]] = entry
            row += 1

        submit_btn = ttk.Button(self, text="Submit", command=self.collect_data)
        submit_btn.grid(row=row, column=0, columnspan=2, pady=10)

    def collect_data(self):
        data = {}
        for field_id, widget in self.entries.items():
            if isinstance(widget, tk.Text):
                data[field_id] = widget.get("1.0", tk.END).strip()
            elif isinstance(widget, tk.Listbox):
                selections = widget.curselection()
                data[field_id] = [widget.get(i) for i in selections]
            else:
                data[field_id] = widget.get()
        print("Collected Form Data:", data)  # Hook this into your update logic
