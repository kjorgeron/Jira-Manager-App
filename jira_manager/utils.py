import tkinter as tk
from tkinter import ttk
import os
import json


def create_jira_card(parent, title, description, aspect_ratio=3.0, radius=20):
    # Create a canvas to draw the rounded background
    canvas = tk.Canvas(parent, bg=parent["bg"], highlightthickness=0)
    canvas.config(width=300, height=100)  # Initial size

    # Create a frame to hold the content
    content = tk.Frame(canvas, bg="white")

    # Add title and description
    tk.Label(
        content,
        text=title,
        font=("Arial", 12, "bold"),
        bg="white",
        anchor="center",
        justify="center",
    ).pack(pady=(5, 2))
    tk.Label(
        content, text=description, wraplength=280, justify="center", bg="white"
    ).pack(pady=(0, 5))

    # Draw rounded rectangle on canvas
    def draw_rounded_rect(w, h):
        canvas.delete("bg")
        x1, y1, x2, y2 = 0, 0, w, h
        r = radius
        points = [
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1,
        ]
        canvas.create_polygon(
            points, fill="white", outline="#ccc", smooth=True, tags="bg"
        )

    # Handle resizing and aspect ratio
    def enforce_aspect(event):
        width = event.width
        height = int(width / aspect_ratio)
        canvas.config(width=width, height=height)
        draw_rounded_rect(width, height)
        canvas.coords("content", width // 2, height // 2)

    # Bind resize event
    canvas.bind("<Configure>", enforce_aspect)

    # Place content in the center of the canvas
    canvas.create_window(0, 0, window=content, anchor="center", tags="content")

    return canvas


def create_toolbar(parent, bg="#4C30EB", padding=10):
    toolbar = tk.Frame(parent, bg=bg, pady=padding)
    toolbar.pack(fill="x", padx=padding, pady=(padding, 0))
    return toolbar


def save_data(payload: dict):
    print(payload)
    path = os.path.join(
        os.environ["USERPROFILE"], "Documents", "jira_manager_settings.json"
    )
    with open(path, "w") as f:
        json.dump(payload, f)


def load_data() -> dict:
    path = os.path.join(
        os.environ["USERPROFILE"], "Documents", "jira_manager_settings.json"
    )

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ JSON file is corrupted. Returning empty config.")
    else:
        print("ℹ️ No config file found. Returning empty config.")

    return {}  # Default empty payload


# def toolbar_action(parent, options: dict, state: dict):
#     # Panel State Manager
#     if state["active_panel"]:
#         state["active_panel"].destroy()
#         state["active_panel"] = None

#     # Logic for Configure Button
#     if options["type"] == "configure":
#         font_style = ("Arial", 12, "bold")
#         selected_auth = tk.StringVar(value="Basic Auth")
#         proxy_option = tk.StringVar(value="No")

#         panel = tk.Frame(parent, bg="white")
#         panel.pack(fill="both", padx=10, pady=10, expand=True)
#         state["active_panel"] = panel

#         # --- Create split layout: form and footer ---
#         form_frame = tk.Frame(panel, bg="white")
#         form_frame.pack(fill="both", expand=True)

#         footer_frame = tk.Frame(panel, bg="white")
#         footer_frame.pack(fill="x", side="bottom")

#         # --- Top Selectors Row ---
#         selector_row = tk.Frame(form_frame, bg="white")
#         selector_row.pack(fill="x", pady=5)

#         tk.Label(
#             selector_row,
#             text="Credential Type:",
#             font=font_style,
#             fg="#4C30EB",
#             bg="white",
#         ).pack(side="left", padx=(0, 5))
#         auth_type = ttk.Combobox(
#             selector_row,
#             textvariable=selected_auth,
#             values=["Basic Auth", "Token Auth"],
#             state="readonly",
#         )
#         auth_type.pack(side="left", padx=(0, 15))

#         tk.Label(
#             selector_row, text="Use Proxies:", font=font_style, fg="#4C30EB", bg="white"
#         ).pack(side="left", padx=(0, 5))
#         proxy_type = ttk.Combobox(
#             selector_row,
#             textvariable=proxy_option,
#             values=["No", "Yes"],
#             state="readonly",
#         )
#         proxy_type.pack(side="left")

#         # --- Separator Line ---
#         ttk.Separator(form_frame, orient="horizontal").pack(fill="x", pady=10)

#         # --- Jira Server Input ---
#         jira_row = tk.Frame(form_frame, bg="white")
#         jira_row.pack(fill="x", pady=5)
#         jira_row.columnconfigure(1, weight=1)
#         tk.Label(
#             jira_row, text="Jira Server:", font=font_style, fg="#4C30EB", bg="white"
#         ).pack(side="left", padx=(0, 5))
#         jira_server_input = tk.Entry(jira_row, font=font_style)
#         jira_server_input.pack(side="left", fill="x", expand=True, padx=10)

#         # --- Proxy Panel ---
#         proxy_panel = tk.Frame(form_frame, bg="white")

#         proxy_http = tk.Frame(proxy_panel, bg="white")
#         proxy_http.pack(fill="x", pady=5)
#         proxy_http.columnconfigure(1, weight=1)
#         tk.Label(
#             proxy_http, text="HTTP Proxy:", font=font_style, fg="#4C30EB", bg="white"
#         ).pack(side="left", padx=(0, 5))
#         http_input = tk.Entry(proxy_http, font=font_style)
#         http_input.pack(side="left", fill="x", expand=True, padx=10)

#         proxy_https = tk.Frame(proxy_panel, bg="white")
#         proxy_https.pack(fill="x", pady=5)
#         proxy_https.columnconfigure(1, weight=1)
#         tk.Label(
#             proxy_https, text="HTTPS Proxy:", font=font_style, fg="#4C30EB", bg="white"
#         ).pack(side="left", padx=(0, 5))
#         https_input = tk.Entry(proxy_https, font=font_style)
#         https_input.pack(side="left", fill="x", expand=True, padx=10)

#         # --- Basic Auth Panel ---
#         basic_panel = tk.Frame(form_frame, bg="white")

#         user_row = tk.Frame(basic_panel, bg="white")
#         user_row.pack(fill="x", pady=5)
#         user_row.columnconfigure(1, weight=1)
#         tk.Label(
#             user_row, text="Username:", font=font_style, fg="#4C30EB", bg="white"
#         ).pack(side="left", padx=(0, 5))
#         username_input = tk.Entry(user_row, font=font_style)
#         username_input.pack(side="left", fill="x", expand=True, padx=10)

#         pass_row = tk.Frame(basic_panel, bg="white")
#         pass_row.pack(fill="x", pady=5)
#         pass_row.columnconfigure(1, weight=1)
#         tk.Label(
#             pass_row, text="Password:", font=font_style, fg="#4C30EB", bg="white"
#         ).pack(side="left", padx=(0, 5))
#         password_input = tk.Entry(pass_row, show="*", font=font_style)
#         password_input.pack(side="left", fill="x", expand=True, padx=10)

#         # --- Token Auth Panel ---
#         token_panel = tk.Frame(form_frame, bg="white")

#         token_row = tk.Frame(token_panel, bg="white")
#         token_row.pack(fill="x", pady=5)
#         token_row.columnconfigure(1, weight=1)
#         tk.Label(
#             token_row, text="Access Token:", font=font_style, fg="#4C30EB", bg="white"
#         ).pack(side="left", padx=(0, 5))
#         token_input = tk.Entry(token_row, show="*", font=font_style)
#         token_input.pack(side="left", fill="x", expand=True, padx=10)

#         # --- Update Logic ---
#         def update_proxy_fields(event=None):
#             proxy_panel.pack_forget()
#             if proxy_option.get() == "Yes":
#                 proxy_panel.pack(fill="x", pady=5)

#         def update_auth_fields(event=None):
#             basic_panel.pack_forget()
#             token_panel.pack_forget()
#             if selected_auth.get() == "Basic Auth":
#                 basic_panel.pack(fill="x", pady=5)
#             else:
#                 token_panel.pack(fill="x", pady=5)

#         proxy_type.bind("<<ComboboxSelected>>", update_proxy_fields)
#         auth_type.bind("<<ComboboxSelected>>", update_auth_fields)

#         update_proxy_fields()
#         update_auth_fields()

#         def on_save():
#             # User Config Data
#             server_data = jira_server_input.get()
#             http_data = http_input.get()
#             https_data = https_input.get()
#             token_data = token_input.get()
#             username_data = username_input.get()
#             password_data = password_input.get()
#             payload = {
#                 "server": server_data,
#                 "http_proxy": http_data,
#                 "https_proxy": https_data,
#                 "token": token_data,
#                 "username": username_data,
#                 "password": password_data,
#             }
#             save_data(payload)
#             toolbar_action(parent, {"type": "configure"}, state)


#         # --- Footer Separator & Save Button ---
#         ttk.Separator(footer_frame, orient="horizontal").pack(fill="x", pady=10)
#         tk.Button(
#             footer_frame,
#             text="Save",
#             font=font_style,
#             bg="white",
#             fg="#4C30EB",
#             command=on_save,
#         ).pack(pady=(5, 10))

#     # Logic for Search Jiras Button
#     elif options["type"] == "search_jiras":
#         panel = tk.Frame(parent, bg="green", bd=2, relief="solid")
#         panel.pack(fill="both", padx=10, pady=10, expand=True)
#         state["active_panel"] = panel

#         # Add content inside the panel (e.g. search bar, labels, etc.)
#         tk.Label(
#             panel,
#             text="Search JIRAs",
#             font=("Arial", 14, "bold"),
#             bg="green",
#             fg="white",
#         ).pack(pady=10)
#         tk.Entry(panel, font=("Arial", 12)).pack(fill="x", padx=20)
#         tk.Button(
#             panel, text="Search", font=("Arial", 12), bg="white", fg="green"
#         ).pack(pady=10)


def toolbar_action(parent, options: dict, state: dict):
    if state["active_panel"]:
        state["active_panel"].destroy()
        state["active_panel"] = None

    if options["type"] == "configure":
        config = load_data()

        font_style = ("Arial", 12, "bold")
        selected_auth = tk.StringVar(value=config.get("auth_type", "Basic Auth"))
        proxy_option = tk.StringVar(
            value=(
                "Yes" if config.get("http_proxy") or config.get("https_proxy") else "No"
            )
        )

        panel = tk.Frame(parent, bg="white")
        panel.pack(fill="both", padx=10, pady=10, expand=True)
        state["active_panel"] = panel

        form_frame = tk.Frame(panel, bg="white")
        form_frame.pack(fill="both", expand=True)

        footer_frame = tk.Frame(panel, bg="white")
        footer_frame.pack(fill="x", side="bottom")

        selector_row = tk.Frame(form_frame, bg="white")
        selector_row.pack(fill="x", pady=5)

        tk.Label(
            selector_row,
            text="Credential Type:",
            font=font_style,
            fg="#4C30EB",
            bg="white",
        ).pack(side="left", padx=(0, 5))
        auth_type = ttk.Combobox(
            selector_row,
            textvariable=selected_auth,
            values=["Basic Auth", "Token Auth"],
            state="readonly",
        )
        auth_type.pack(side="left", padx=(0, 15))

        tk.Label(
            selector_row, text="Use Proxies:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        proxy_type = ttk.Combobox(
            selector_row,
            textvariable=proxy_option,
            values=["No", "Yes"],
            state="readonly",
        )
        proxy_type.pack(side="left")

        ttk.Separator(form_frame, orient="horizontal").pack(fill="x", pady=10)

        jira_row = tk.Frame(form_frame, bg="white")
        jira_row.pack(fill="x", pady=5)
        jira_row.columnconfigure(1, weight=1)
        tk.Label(
            jira_row, text="Jira Server:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        jira_server_input = tk.Entry(jira_row, font=font_style)
        jira_server_input.pack(side="left", fill="x", expand=True, padx=10)
        jira_server_input.insert(0, config.get("server", ""))

        proxy_panel = tk.Frame(form_frame, bg="white")

        proxy_http = tk.Frame(proxy_panel, bg="white")
        proxy_http.pack(fill="x", pady=5)
        proxy_http.columnconfigure(1, weight=1)
        tk.Label(
            proxy_http, text="HTTP Proxy:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        http_input = tk.Entry(proxy_http, font=font_style)
        http_input.pack(side="left", fill="x", expand=True, padx=10)
        http_input.insert(0, config.get("http_proxy", ""))

        proxy_https = tk.Frame(proxy_panel, bg="white")
        proxy_https.pack(fill="x", pady=5)
        proxy_https.columnconfigure(1, weight=1)
        tk.Label(
            proxy_https, text="HTTPS Proxy:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        https_input = tk.Entry(proxy_https, font=font_style)
        https_input.pack(side="left", fill="x", expand=True, padx=10)
        https_input.insert(0, config.get("https_proxy", ""))

        basic_panel = tk.Frame(form_frame, bg="white")

        user_row = tk.Frame(basic_panel, bg="white")
        user_row.pack(fill="x", pady=5)
        user_row.columnconfigure(1, weight=1)
        tk.Label(
            user_row, text="Username:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        username_input = tk.Entry(user_row, font=font_style)
        username_input.pack(side="left", fill="x", expand=True, padx=10)
        username_input.insert(0, config.get("username", ""))

        pass_row = tk.Frame(basic_panel, bg="white")
        pass_row.pack(fill="x", pady=5)
        pass_row.columnconfigure(1, weight=1)
        tk.Label(
            pass_row, text="Password:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        password_input = tk.Entry(pass_row, show="*", font=font_style)
        password_input.pack(side="left", fill="x", expand=True, padx=10)
        password_input.insert(0, config.get("password", ""))

        token_panel = tk.Frame(form_frame, bg="white")

        token_row = tk.Frame(token_panel, bg="white")
        token_row.pack(fill="x", pady=5)
        token_row.columnconfigure(1, weight=1)
        tk.Label(
            token_row, text="Access Token:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        token_input = tk.Entry(token_row, show="*", font=font_style)
        token_input.pack(side="left", fill="x", expand=True, padx=10)
        token_input.insert(0, config.get("token", ""))

        def update_proxy_fields(event=None):
            proxy_panel.pack_forget()
            if proxy_option.get() == "Yes":
                proxy_panel.pack(fill="x", pady=5)

        def update_auth_fields(event=None):
            basic_panel.pack_forget()
            token_panel.pack_forget()
            if selected_auth.get() == "Basic Auth":
                basic_panel.pack(fill="x", pady=5)
            else:
                token_panel.pack(fill="x", pady=5)

        proxy_type.bind("<<ComboboxSelected>>", update_proxy_fields)
        auth_type.bind("<<ComboboxSelected>>", update_auth_fields)

        update_proxy_fields()
        update_auth_fields()

        def on_save():

            # Handles clearing of unused data for login
            if selected_auth.get() == "Basic Auth":
                token_input.delete(0, tk.END)
            else:  # Token Auth selected
                username_input.delete(0, tk.END)
                password_input.delete(0, tk.END)

            # Handles clearing of unused data for proxy
            if proxy_option.get() == "No":
                http_input.delete(0, tk.END)
                https_input.delete(0, tk.END)

            payload = {
                "server": jira_server_input.get(),
                "http_proxy": http_input.get(),
                "https_proxy": https_input.get(),
                "token": token_input.get(),
                "username": username_input.get(),
                "password": password_input.get(),
                "auth_type": selected_auth.get(),
            }
            save_data(payload)
            toolbar_action(parent, {"type": "configure"}, state)

        ttk.Separator(footer_frame, orient="horizontal").pack(fill="x", pady=10)
        tk.Button(
            footer_frame,
            text="Save",
            font=font_style,
            bg="white",
            fg="#4C30EB",
            command=on_save,
        ).pack(pady=(5, 10))
