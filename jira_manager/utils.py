import tkinter as tk
import os
import json
import requests
import base64
from tkinter import ttk
from jira import JIRAError, JIRA
from requests.auth import HTTPBasicAuth
from jira_manager.custom_widgets import EntryWithPlaceholder, ScrollableFrame
from pprint import pprint


def create_scrollable_frame(parent):
    # Base canvas to enable scrolling
    canvas = tk.Canvas(parent, bg="white", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # Hidden scrollbar (scroll logic still enabled)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack_forget()

    # This frame is where you’ll add your actual content
    scrollable_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Update scroll region on content change
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # Enable mousewheel scrolling (Windows/Linux)
    scrollable_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    return scrollable_frame


def encode_basic_auth(username: str, password: str) -> str:
    credentials = f"{username}:{password}"
    token_bytes = credentials.encode("utf-8")
    base64_token = base64.b64encode(token_bytes).decode("utf-8")
    return base64_token


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
        font=("Trebuchet MS", 12, "bold"),
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


def generate_error(parent, message: str):
    # Outer shield-frame (red border)
    border_frame = tk.Frame(parent, bg="red", padx=3, pady=3)  # Blood-red Viking steel

    # Canvas scrollable battleboard
    canvas = tk.Canvas(border_frame, bg="#fdfdfd", highlightthickness=0, width=550, height=100)
    canvas.pack(fill="both", expand=True)

    # Hidden scrollbar (still battle-ready)
    scrollbar = tk.Scrollbar(border_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack_forget()

    # Scrollable content terrain
    content_frame = tk.Frame(canvas, bg="#fdfdfd")
    canvas.create_window((0, 0), window=content_frame, anchor="nw")

    # Expand scroll bounds as messages grow
    content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Enable trackpad & mousewheel charge
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    # The error rune itself
    tk.Label(
        content_frame,
        text=f"⚠️ Error Occurred:\n\n{message}",
        font=("Trebuchet MS", 12, "bold"),  # Clean, heroic font
        fg="red",
        bg="#fdfdfd",
        wraplength=500,
        justify="left",
        padx=12,
        pady=12,
    ).pack(fill="x")

    return border_frame


def configure_results(results, options, parent, state):
    # Handling of Jira Data
    try:
        # Handlers for improper JQL queries
        if results["errorMessages"]:
            raise Exception(f"{results["errorMessages"]}")
        if options["jql"] != "Enter proper JQL query..." or options["jql"] != "":
            
            pprint(f"{results=}")
            
            # CREATE SCROLLABLE FRAME FOR JIRA CARDS
        else:
            raise Exception("Please provide proper jql query...")
    except Exception as e:
        # error_frame = generate_error(
        #     parent,
        #     f"{e}",
        # )
        scroll_area = create_scrollable_frame(parent)
        scroll_area.pack(fill="both", padx=10, expand=True)
        error_message = generate_error(scroll_area, f"{'Error occurred with the JQL query... Please provide a proper query'}")
        error_message.pack()


        # error_frame.pack()
        # state["active_panel"] = error_frame

    # except Exception as e:
    #     # Create a scrollable container for the error panel
    #     scroll_container = ScrollableFrame(parent)
    #     scroll_container.pack(fill="both", expand=True)

    #     # Generate the error frame inside the scrollable area
    #     error_frame = generate_error(scroll_container.scrollable_frame, str(e))
    #     error_frame.pack(padx=10, pady=10)

    #     # Track active panel
    #     state["active_panel"] = scroll_container



def toolbar_action(parent, options: dict, state: dict):
    # Handling of active frames
    if state["active_panel"]:
        state["active_panel"].destroy()
        state["active_panel"] = None

    # Handling of Data Configuration
    if options["type"] == "configure":

        # Data stored in users Documents folder
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

        # Form Inputs
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
            user_row, text="User ID:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        username_input = EntryWithPlaceholder(
            user_row,
            placeholder="Enter username or email...",
            color="grey",
            font=font_style,
            initial_text=config.get("username", ""),
        )
        username_input.pack(side="left", fill="x", expand=True, padx=10)

        pass_row = tk.Frame(basic_panel, bg="white")
        pass_row.pack(fill="x", pady=5)
        pass_row.columnconfigure(1, weight=1)
        tk.Label(
            pass_row, text="Password:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        password_input = EntryWithPlaceholder(
            pass_row,
            placeholder="Enter password or token...",
            color="grey",
            show="*",
            font=font_style,
            initial_text=config.get("password", ""),
        )
        password_input.pack(side="left", fill="x", expand=True, padx=10)

        token_panel = tk.Frame(form_frame, bg="white")

        token_row = tk.Frame(token_panel, bg="white")
        token_row.pack(fill="x", pady=5)
        token_row.columnconfigure(1, weight=1)
        tk.Label(
            token_row, text="Access Token:", font=font_style, fg="#4C30EB", bg="white"
        ).pack(side="left", padx=(0, 5))
        token_input = EntryWithPlaceholder(
            token_row,
            placeholder="(Bearer Token) JWT or OAuth 2.0 only...",
            color="grey",
            show="*",
            font=font_style,
            initial_text=config.get("token", ""),
        )
        token_input.pack(side="left", fill="x", expand=True, padx=10)

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

            # Helper to ignore placeholder text when saving
            def get_clean_value(widget):
                value = widget.get()
                if (
                    value != widget.placeholder
                    or widget["fg"] != widget.placeholder_color
                ):
                    return value
                return ""

            payload = {
                "server": jira_server_input.get(),
                "http_proxy": http_input.get(),
                "https_proxy": https_input.get(),
                "token": get_clean_value(token_input),
                "username": get_clean_value(username_input),
                "password": get_clean_value(password_input),
                "auth_type": selected_auth.get(),
                "proxy_option": proxy_option.get(),
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

    # Handling of Jira Searching
    elif options["type"] == "search_jiras":
        data = load_data()
        if data != {}:
            server = data["server"]
            token = data["token"]
            username = data["username"]
            password = data["password"]
            http_proxy = data["http_proxy"]
            https_proxy = data["https_proxy"]
            use_proxy = data["proxy_option"]

            if server != "":
                # Handles credential initialization
                if token != "":
                    try:
                        # jira = JIRA(server=server, token_auth=token)
                        headers = {
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        }
                    except JIRAError as e:
                        error_frame = generate_error(
                            parent,
                            f"Issue with token - {e}",
                        )
                    error_frame.pack()
                    state["active_panel"] = error_frame
                    raise JIRAError
                elif username != "" and password != "":
                    try:
                        headers = {
                            "Authorization": f"Basic {encode_basic_auth(username, password)}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        }
                    except JIRAError as e:
                        error_frame = generate_error(
                            parent,
                            f"Issue with username/password - {e}",
                        )
                        error_frame.pack()
                        state["active_panel"] = error_frame
                        raise JIRAError
                else:
                    error_frame = generate_error(
                        parent,
                        "Missing login credentials.",
                    )
                    error_frame.pack()
                    state["active_panel"] = error_frame

                # No proxy request
                if use_proxy.lower() != "yes":
                    # jql = "key = SCRUM-1"
                    url = f"{server}rest/api/2/search?jql={options['jql']}"
                    try:
                        if options["jql"] != "Enter proper JQL query...":
                            response = requests.get(url=url, headers=headers)

                            # Return value
                            results = response.json()
                            configure_results(results, options, parent, state)
                        else:
                            raise Exception("Please provide proper jql query")
                    except Exception as e:
                        error_frame = generate_error(
                            parent,
                            f"{e}",
                        )
                        error_frame.pack()
                        state["active_panel"] = error_frame

                # Handles proxy requests
                if use_proxy.lower() != "no":
                    if (
                        http_proxy != ""
                        and https_proxy != ""
                        and use_proxy.lower() == "yes"
                    ):
                        proxy = {"http": http_proxy, "https": https_proxy}
                        # DO REQUEST USING PROXY
                        url = f"{server}rest/api/2/search?jql={options['jql']}"
                        try:
                            # if options["jql"] != "Enter proper JQL query...":
                            response = requests.get(
                                url=url, headers=headers, proxies=proxy
                            )

                            # Return value
                            results = response.json()
                            configure_results(results, options, parent, state)
                            # else:
                            #     raise Exception("Please provide proper jql query")
                        except JIRAError as e:
                            error_frame = generate_error(
                                parent,
                                f"{e}",
                            )
                            error_frame.pack()
                            state["active_panel"] = error_frame

                    elif (
                        use_proxy.lower() == "yes"
                        and http_proxy == ""
                        or https_proxy == ""
                    ):
                        error_frame = generate_error(
                            parent,
                            "Must have values in both HTTP and HTTPS proxies in order to use.",
                        )
                        error_frame.pack()
                        state["active_panel"] = error_frame
            else:
                error_frame = generate_error(
                    parent,
                    "Missing Jira server url.",
                )
                error_frame.pack()
                state["active_panel"] = error_frame
                raise Exception
        else:
            print("No data")
            error_frame = generate_error(
                parent,
                "No Configuration Data found... please press Configure button at top left.",
            )
            error_frame.pack(fill="both", padx=10)
            state["active_panel"] = error_frame
