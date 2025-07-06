import tkinter as tk
from tkinter import ttk


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


def create_button(parent, text, command, **style):
    return tk.Button(parent, text=text, command=command, **style)

# def toolbar_action(parent, options: dict, state: dict):
#     if state["active_panel"]:
#         state["active_panel"].destroy()
#         state["active_panel"] = None

#     if not options or options["type"] != "configure":
#         return

#     panel = tk.Frame(parent, bg="blue")
#     panel.pack(fill="both", padx=10, pady=10, expand=1)
#     state["active_panel"] = panel

#     font_style = ("Arial", 12, "bold")
#     selected_auth = tk.StringVar(value="Basic Auth")
#     proxy_option = tk.StringVar(value="No")

#     # --- Top Selectors ---
#     tk.Label(panel, text="Credential Type:", font=font_style, fg="white", bg="blue")\
#         .grid(row=0, column=0, sticky="e", padx=5, pady=5)
#     auth_type = ttk.Combobox(panel, textvariable=selected_auth,
#                              values=["Basic Auth", "Token Auth"], state="readonly")
#     auth_type.grid(row=0, column=1, sticky="w", padx=5, pady=5)

#     tk.Label(panel, text="Use Proxies:", font=font_style, fg="white", bg="blue")\
#         .grid(row=0, column=2, sticky="e", padx=5, pady=5)
#     proxy_type = ttk.Combobox(panel, textvariable=proxy_option,
#                               values=["No", "Yes"], state="readonly")
#     proxy_type.grid(row=0, column=3, sticky="w", padx=5, pady=5)

#     # --- Separator ---
#     ttk.Separator(panel, orient="horizontal")\
#         .grid(row=1, column=0, columnspan=4, sticky="ew", pady=10)

#     # --- Jira Server ---
#     tk.Label(panel, text="Jira Server:", font=font_style, fg="white", bg="blue")\
#         .grid(row=2, column=0, sticky="e", padx=5, pady=5)
#     tk.Entry(panel, font=font_style)\
#         .grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=5)

#     # --- Proxy Panel ---
#     proxy_panel = tk.Frame(panel, bg="blue")
#     tk.Label(proxy_panel, text="HTTP Proxy:", font=font_style, fg="white", bg="blue")\
#         .grid(row=0, column=0, sticky="e", padx=5, pady=5)
#     tk.Entry(proxy_panel, font=font_style)\
#         .grid(row=0, column=1, sticky="ew", padx=5, pady=5)
#     tk.Label(proxy_panel, text="HTTPS Proxy:", font=font_style, fg="white", bg="blue")\
#         .grid(row=1, column=0, sticky="e", padx=5, pady=5)
#     tk.Entry(proxy_panel, font=font_style)\
#         .grid(row=1, column=1, sticky="ew", padx=5, pady=5)
#     proxy_panel.columnconfigure(1, weight=1)

#     # --- Credential Panels ---
#     basic_panel = tk.Frame(panel, bg="blue")
#     tk.Label(basic_panel, text="Username:", font=font_style, fg="white", bg="blue")\
#         .grid(row=0, column=0, sticky="e", padx=5, pady=5)
#     tk.Entry(basic_panel, font=font_style)\
#         .grid(row=0, column=1, sticky="ew", padx=5, pady=5)
#     tk.Label(basic_panel, text="Password:", font=font_style, fg="white", bg="blue")\
#         .grid(row=1, column=0, sticky="e", padx=5, pady=5)
#     tk.Entry(basic_panel, show="*", font=font_style)\
#         .grid(row=1, column=1, sticky="ew", padx=5, pady=5)
#     basic_panel.columnconfigure(1, weight=1)

#     token_panel = tk.Frame(panel, bg="blue")
#     tk.Label(token_panel, text="Access Token:", font=font_style, fg="white", bg="blue")\
#         .grid(row=0, column=0, sticky="e", padx=5, pady=5)
#     tk.Entry(token_panel, show="*", font=font_style)\
#         .grid(row=0, column=1, sticky="ew", padx=5, pady=5)
#     token_panel.columnconfigure(1, weight=1)

#     # --- Column Stretching ---
#     panel.columnconfigure(1, weight=1)
#     panel.columnconfigure(3, weight=1)

#     # --- Update Logic ---
#     def update_proxy_fields(event=None):
#         proxy_panel.grid_remove()
#         if proxy_option.get() == "Yes":
#             proxy_panel.grid(row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

#     def update_auth_fields(event=None):
#         basic_panel.grid_remove()
#         token_panel.grid_remove()
#         if selected_auth.get() == "Basic Auth":
#             basic_panel.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
#         else:
#             token_panel.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

#     auth_type.bind("<<ComboboxSelected>>", update_auth_fields)
#     proxy_type.bind("<<ComboboxSelected>>", update_proxy_fields)

#     update_proxy_fields()
#     update_auth_fields()

def toolbar_action(parent, options: dict, state: dict):
    if state["active_panel"]:
        state["active_panel"].destroy()
        state["active_panel"] = None

    if not options or options["type"] != "configure":
        return

    font_style = ("Arial", 12, "bold")
    selected_auth = tk.StringVar(value="Basic Auth")
    proxy_option = tk.StringVar(value="No")

    panel = tk.Frame(parent, bg="blue")
    panel.pack(fill="both", padx=10, pady=10, expand=True)
    state["active_panel"] = panel

    # --- Top Selectors Row ---
    selector_row = tk.Frame(panel, bg="blue")
    selector_row.pack(fill="x", pady=5)

    tk.Label(selector_row, text="Credential Type:", font=font_style, fg="white", bg="blue")\
        .pack(side="left", padx=(0, 5))
    auth_type = ttk.Combobox(selector_row, textvariable=selected_auth,
                             values=["Basic Auth", "Token Auth"], state="readonly")
    auth_type.pack(side="left", padx=(0, 15))

    tk.Label(selector_row, text="Use Proxies:", font=font_style, fg="white", bg="blue")\
        .pack(side="left", padx=(0, 5))
    proxy_type = ttk.Combobox(selector_row, textvariable=proxy_option,
                              values=["No", "Yes"], state="readonly")
    proxy_type.pack(side="left")

    # --- Separator Line ---
    ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=10)

    # --- Jira Server Input ---
    jira_row = tk.Frame(panel, bg="blue")
    jira_row.pack(fill="x", pady=5)
    jira_row.columnconfigure(1, weight=1)
    tk.Label(jira_row, text="Jira Server:", font=font_style, fg="white", bg="blue")\
        .pack(side="left", padx=(0, 5))
    tk.Entry(jira_row, font=font_style).pack(side="left", fill="x", expand=True, padx=10)

    # --- Proxy Panel ---
    proxy_panel = tk.Frame(panel, bg="blue")

    proxy_http = tk.Frame(proxy_panel, bg="blue")
    proxy_http.pack(fill="x", pady=5)
    proxy_http.columnconfigure(1, weight=1)
    tk.Label(proxy_http, text="HTTP Proxy:", font=font_style, fg="white", bg="blue")\
        .pack(side="left", padx=(0, 5))
    tk.Entry(proxy_http, font=font_style).pack(side="left", fill="x", expand=True, padx=10)

    proxy_https = tk.Frame(proxy_panel, bg="blue")
    proxy_https.pack(fill="x", pady=5)
    proxy_https.columnconfigure(1, weight=1)
    tk.Label(proxy_https, text="HTTPS Proxy:", font=font_style, fg="white", bg="blue")\
        .pack(side="left", padx=(0, 5))
    tk.Entry(proxy_https, font=font_style).pack(side="left", fill="x", expand=True, padx=10)

    # --- Basic Auth Panel ---
    basic_panel = tk.Frame(panel, bg="blue")

    user_row = tk.Frame(basic_panel, bg="blue")
    user_row.pack(fill="x", pady=5)
    user_row.columnconfigure(1, weight=1)
    tk.Label(user_row, text="Username:", font=font_style, fg="white", bg="blue")\
        .pack(side="left", padx=(0, 5))
    tk.Entry(user_row, font=font_style).pack(side="left", fill="x", expand=True, padx=10)

    pass_row = tk.Frame(basic_panel, bg="blue")
    pass_row.pack(fill="x", pady=5)
    pass_row.columnconfigure(1, weight=1)
    tk.Label(pass_row, text="Password:", font=font_style, fg="white", bg="blue")\
        .pack(side="left", padx=(0, 5))
    tk.Entry(pass_row, show="*", font=font_style).pack(side="left", fill="x", expand=True, padx=10)

    # --- Token Auth Panel ---
    token_panel = tk.Frame(panel, bg="blue")

    token_row = tk.Frame(token_panel, bg="blue")
    token_row.pack(fill="x", pady=5)
    token_row.columnconfigure(1, weight=1)
    tk.Label(token_row, text="Access Token:", font=font_style, fg="white", bg="blue")\
        .pack(side="left", padx=(0, 5))
    tk.Entry(token_row, show="*", font=font_style).pack(side="left", fill="x", expand=True, padx=10)

    # --- Update Logic ---
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