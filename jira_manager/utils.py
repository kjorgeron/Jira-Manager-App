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
from PIL import Image, ImageTk
from jira_manager.file_manager import save_data, load_data
from jira_manager.themes import ThemeManager, light_mode, dark_mode


def initialize_window():
    root = tk.Tk()
    # root.configure(bg=background)
    root.title("TicketSmith")
    root.geometry("600x800")
    icon_path = "images/ticket-smith-icon.png"
    img = Image.open(icon_path)
    resized_img = img.resize((32, 32), Image.Resampling.LANCZOS)
    icon = ImageTk.PhotoImage(resized_img)
    root.iconphoto(False, icon)
    root.minsize(800, 600) 
    return root

def clear_focus(event, root):
        widget_class = str(event.widget.winfo_class())
        allowed_classes = (
            "Entry", "TEntry", "TCombobox", "Text", "Custom.TCombobox",
            "Listbox", "Button", "Checkbutton", "Radiobutton"
        )
        if widget_class not in allowed_classes:
            root.focus_set()

def get_theme_mode(config_path="app_config.json"):
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            # print("theme=", config["theme"])
            theme = config.get("theme", "light")  # Default to light
            return theme.lower()
    except Exception as e:
        # print(f"Error loading config: {e}")
        return "light"  # Fallback


def create_divider(parent, bg_color):
    # --- Divider (optional) ---
    divider = tk.Frame(parent, bg=bg_color, height=2)
    divider.pack(fill=tk.X, padx=10)


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
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # Enable mousewheel scrolling (Windows/Linux)
    scrollable_frame.bind_all(
        "<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units")
    )

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


def generate_error(parent, message: str, mode: dict, theme_manager: ThemeManager):
    
    # Outer shield-frame (red border)
    border_frame = tk.Frame(parent, padx=3, pady=3)  # Blood-red Viking steel
    theme_manager.register(border_frame, "error_border_frame")

    # Canvas scrollable battleboard
    canvas = tk.Canvas(border_frame, width=550, height=100)
    canvas.pack(fill="both", expand=True)
    theme_manager.register(canvas, "error_canvas")

    # Hidden scrollbar (still battle-ready)
    scrollbar = tk.Scrollbar(border_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack_forget()

    # Scrollable content terrain
    content_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=content_frame, anchor="nw")
    theme_manager.register(content_frame, "frame")

    # Expand scroll bounds as messages grow
    content_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # Enable trackpad & mousewheel charge
    canvas.bind_all(
        "<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units")
    )

    # The error rune itself
    error_label = tk.Label(
        content_frame,
        text=f"⚠️ Error Occurred:\n\n{message}",
        wraplength=500,
        justify="left",
        padx=12,
        pady=12,
    )
    error_label.pack(fill="x")
    theme_manager.register(error_label, "error_label")
    return border_frame


def configure_results(results, options, parent, state, mode, theme_manager, panel_choice):
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
        # error_message = generate_error(
        #     scroll_area,
        #     f"{'Error occurred with the JQL query... Please provide a proper query'}",
        #     mode,
        #     theme_manager,
        # )
        # error_message.pack()
        panel_choice["error_panel"].update_message("Missing login credentials")
        state["active_panel"] = panel_choice["error_panel"].pack()

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


# def toolbar_action(
#     parent,
#     options: dict,
#     state: dict,
#     mode: dict,
#     theme_manager: ThemeManager,
#     active_panels: list,
#     panel_choice: dict
# ):



#     if state["active_panel"]:
#         state["active_panel"].pack_forget()
#         # state["active_panel"].destroy()
#         state["active_panel"] = None

#     # # Handling of Data Configuration
#     if options["type"] == "configure":
#         from jira_manager.custom_panels import ConfigurationFormBuilder
#         # config = ConfigurationFormBuilder(parent, dark_mode=dark_mode, light_mode=light_mode, theme_manager=theme_manager, padx=10, pady=10)
#         # config.pack(fill="x")
#         # theme_manager.register(config, "frame")
#         # config_form = config.build_form()
#         # config_form.pack(expand=True, fill="x")
#         # theme_manager.register(config_form, "frame")
#         state["active_panel"] = panel_choice["configure_panel"].pack(fill="x")

#     #     # Data stored in users Documents folder
#     #     config = load_data()
#     #     font_style = ("Arial", 12, "bold")

#     #     # DEFAULTS FOR COMBOBOX
#     #     selected_auth = tk.StringVar(value=config.get("auth_type", "Basic Auth"))
#     #     proxy_option = tk.StringVar(
#     #         value=(
#     #             "Yes" if config.get("http_proxy") or config.get("https_proxy") else "No"
#     #         )
#     #     )
#     #     theme_option = tk.StringVar(
#     #         value=config.get("theme", "Light")  # default to 'light' if not set
#     #     )

#     #     panel = tk.Frame(parent)
#     #     panel.pack(fill="both", padx=10, pady=10, expand=True)
#     #     state["active_panel"] = panel
#     #     active_panels.append(panel)
#     #     theme_manager.register(panel, "frame")

#     #     form_frame = tk.Frame(panel)
#     #     form_frame.pack(fill="both", expand=True)
#     #     theme_manager.register(form_frame, "frame")

#     #     footer_frame = tk.Frame(panel)
#     #     footer_frame.pack(fill="x", side="bottom")
#     #     theme_manager.register(footer_frame, "frame")

#     #     selector_row = tk.Frame(form_frame)
#     #     selector_row.pack(fill="x", pady=5)
#     #     theme_manager.register(selector_row, "frame")

#     #     # Row 0, Column 0 – Credential Type
#     #     cred_label = tk.Label(
#     #         selector_row,
#     #         text="Credential Type:",
#     #         font=font_style,
#     #     )
#     #     cred_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
#     #     theme_manager.register(cred_label, "label")

#     #     auth_type = ttk.Combobox(
#     #         selector_row,
#     #         textvariable=selected_auth,
#     #         values=["Basic Auth", "Token Auth"],
#     #         state="readonly",
#     #         style="Custom.TCombobox",
#     #     )
#     #     auth_type.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=2)
#     #     theme_manager.register(auth_type, "combobox")

#     #     # Row 0, Column 2 – Use Proxies
#     #     proxy_label = tk.Label(
#     #         selector_row,
#     #         text="Use Proxies:",
#     #         font=font_style,
#     #     )
#     #     proxy_label.grid(row=0, column=2, sticky="w", padx=(0, 5), pady=2)
#     #     theme_manager.register(proxy_label, "label")

#     #     proxy_type = ttk.Combobox(
#     #         selector_row,
#     #         textvariable=proxy_option,
#     #         values=["No", "Yes"],
#     #         state="readonly",
#     #         style="Custom.TCombobox",
#     #     )
#     #     proxy_type.grid(row=0, column=3, sticky="ew", pady=2)
#     #     theme_manager.register(proxy_type, "combobox")

#     #     # Row 1, Column 1 – Theme
#     #     theme_label = tk.Label(
#     #         selector_row,
#     #         text="Theme:",
#     #         font=font_style,
#     #     )
#     #     theme_label.grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
#     #     theme_manager.register(theme_label, "label")

#     #     theme = ttk.Combobox(
#     #         selector_row,
#     #         textvariable=theme_option,
#     #         values=["Light", "Dark"],
#     #         state="readonly",
#     #         style="Custom.TCombobox",
#     #     )
#     #     theme.grid(row=1, column=1, sticky="ew", pady=2)
#     #     theme_manager.register(theme, "combobox")

#     #     # SEPERATOR IN FORM
#     #     ttk.Separator(form_frame, orient="horizontal").pack(fill="x", pady=10)

#     #     # Form Inputs
#     #     jira_row = tk.Frame(form_frame)
#     #     jira_row.pack(fill="x", pady=5)
#     #     jira_row.columnconfigure(1, weight=1)
#     #     theme_manager.register(jira_row, "frame")

#     #     server_label = tk.Label(
#     #         jira_row,
#     #         text="Jira Server:",
#     #         font=font_style,
#     #     )
#     #     server_label.pack(side="left", padx=(0, 5))
#     #     theme_manager.register(server_label, "label")

#     #     jira_server_input = EntryWithPlaceholder(
#     #         jira_row,
#     #         placeholder="Provide base url",
#     #         font=font_style,
#     #         initial_text=config.get("server", ""),
#     #     )
#     #     jira_server_input.pack(side="left", fill="x", expand=True, padx=10)
#     #     theme_manager.register(jira_server_input, "placeholder_entry")

#     #     proxy_panel = tk.Frame(form_frame)

#     #     proxy_http = tk.Frame(proxy_panel)
#     #     proxy_http.pack(fill="x", pady=5)
#     #     proxy_http.columnconfigure(1, weight=1)
#     #     theme_manager.register(proxy_http, "frame")

#     #     http_label = tk.Label(
#     #         proxy_http,
#     #         text="HTTP Proxy:",
#     #         font=font_style,
#     #     )
#     #     http_label.pack(side="left", padx=(0, 5))
#     #     theme_manager.register(http_label, "label")

#     #     http_input = tk.Entry(
#     #         proxy_http,
#     #     )
#     #     http_input.pack(side="left", fill="x", expand=True, padx=10)
#     #     http_input.insert(0, config.get("http_proxy", ""))
#     #     theme_manager.register(http_input, "entry")

#     #     proxy_https = tk.Frame(proxy_panel)
#     #     proxy_https.pack(fill="x", pady=5)
#     #     proxy_https.columnconfigure(1, weight=1)
#     #     theme_manager.register(proxy_https, "frame")

#     #     https_label = tk.Label(
#     #         proxy_https,
#     #         text="HTTPS Proxy:",
#     #         font=font_style,
#     #     )
#     #     https_label.pack(side="left", padx=(0, 5))
#     #     theme_manager.register(https_label, "label")

#     #     https_input = tk.Entry(
#     #         proxy_https,
#     #     )
#     #     https_input.pack(side="left", fill="x", expand=True, padx=10)
#     #     https_input.insert(0, config.get("https_proxy", ""))
#     #     theme_manager.register(https_input, "entry")

#     #     basic_panel = tk.Frame(form_frame)

#     #     user_row = tk.Frame(basic_panel)
#     #     user_row.pack(fill="x", pady=5)
#     #     user_row.columnconfigure(1, weight=1)
#     #     theme_manager.register(user_row, "frame")

#     #     user_label = tk.Label(
#     #         user_row,
#     #         text="User ID:",
#     #         font=font_style,
#     #     )
#     #     user_label.pack(side="left", padx=(0, 5))
#     #     theme_manager.register(user_label, "label")

#     #     username_input = EntryWithPlaceholder(
#     #         user_row,
#     #         placeholder="Enter username or email",
#     #         initial_text=config.get("username", ""),
#     #     )
#     #     username_input.pack(side="left", fill="x", expand=True, padx=10)
#     #     theme_manager.register(username_input, "placeholder_entry")

#     #     pass_row = tk.Frame(basic_panel)
#     #     pass_row.pack(fill="x", pady=5)
#     #     pass_row.columnconfigure(1, weight=1)
#     #     theme_manager.register(pass_row, "frame")

#     #     pass_label = tk.Label(
#     #         pass_row,
#     #         text="Password:",
#     #         font=font_style,
#     #     )
#     #     pass_label.pack(side="left", padx=(0, 5))
#     #     theme_manager.register(pass_label, "label")

#     #     password_input = EntryWithPlaceholder(
#     #         pass_row,
#     #         placeholder="Enter password or token",
#     #         show="*",
#     #     )
#     #     password_input.pack(side="left", fill="x", expand=True, padx=10)
#     #     theme_manager.register(password_input, "placeholder_entry")

#     #     token_panel = tk.Frame(form_frame)

#     #     token_row = tk.Frame(token_panel)
#     #     token_row.pack(fill="x", pady=5)
#     #     token_row.columnconfigure(1, weight=1)
#     #     theme_manager.register(token_row, "frame")

#     #     token_label = tk.Label(
#     #         token_row,
#     #         text="Access Token:",
#     #         font=font_style,
#     #     )
#     #     token_label.pack(side="left", padx=(0, 5))
#     #     theme_manager.register(token_label, "label")

#     #     token_input = EntryWithPlaceholder(
#     #         token_row,
#     #         placeholder="(Bearer Token) JWT or OAuth 2.0 only",
#     #         show="*",
#     #         initial_text=config.get("token", ""),
#     #     )
#     #     token_input.pack(side="left", fill="x", expand=True, padx=10)
#     #     theme_manager.register(token_input, "placeholder_entry")

#     #     proxy_type.bind("<<ComboboxSelected>>", update_proxy_fields)
#     #     auth_type.bind("<<ComboboxSelected>>", update_auth_fields)

#     #     update_proxy_fields()
#     #     update_auth_fields()

#     #     ttk.Separator(footer_frame, orient="horizontal").pack(fill="x", pady=10)
#     #     save_button = tk.Button(
#     #         footer_frame,
#     #         text="Save",
#     #         command=lambda: on_save(theme_manager),
#     #     )
#     #     save_button.pack(pady=(5, 10))
#     #     theme_manager.register(save_button, "base_button")

#     # Handling of Jira Searching
#     elif options["type"] == "search_jiras":
#         data = load_data()
#         if data != {}:
#             # NEEDS EXCEPTION HERE FOR MISSING CONFIG ITEMS
#             try:
#                 server = data["server"]
#                 token = data["token"]
#                 username = data["username"]
#                 password = data["password"]
#                 http_proxy = data["http_proxy"]
#                 https_proxy = data["https_proxy"]
#                 use_proxy = data["proxy_option"]
#             except Exception:
#                 # error_frame = generate_error(
#                 #     parent,
#                 #     "Missing required fields in Configure file",
#                 #     mode,
#                 #     theme_manager,
#                 # )
#                 # error_frame.pack()
#                 # state["active_panel"] = error_frame
#                 # active_panels.append(error_frame)
#                 panel_choice["error_panel"].update_message("Missing login credentials")
#                 state["active_panel"] = panel_choice["error_panel"].pack()

#             if server != "":
#                 # Handles credential initialization
#                 if token != "":
#                     try:
#                         # jira = JIRA(server=server, token_auth=token)
#                         headers = {
#                             "Authorization": f"Bearer {token}",
#                             "Content-Type": "application/json",
#                             "Accept": "application/json",
#                         }
#                     except JIRAError as e:
#                     #     error_frame = generate_error(
#                     #         parent, f"Issue with token - {e}", mode, theme_manager
#                     #     )
#                     # error_frame.pack()
#                     # state["active_panel"] = error_frame
#                     # active_panels.append(error_frame)
#                         panel_choice["error_panel"].update_message(f"Issue with token - {e}")
#                     raise JIRAError
#                 elif username != "" and password != "":
#                     try:
#                         headers = {
#                             "Authorization": f"Basic {encode_basic_auth(username, password)}",
#                             "Content-Type": "application/json",
#                             "Accept": "application/json",
#                         }
#                     except JIRAError as e:
#                         # error_frame = generate_error(
#                         #     parent,
#                         #     f"Issue with username/password - {e}",
#                         #     mode,
#                         #     theme_manager,
#                         # )
#                         # error_frame.pack()
#                         # state["active_panel"] = error_frame
#                         # active_panels.append(error_frame)
#                         panel_choice["error_panel"].update_message("Missing login credentials")
#                         state["active_panel"] = panel_choice["error_panel"].pack()
#                         raise JIRAError
#                 # """NEED TO FIX UI ERROR FOR THIS ERROR MESSAGE"""
#                 else:
#                     # error_frame = generate_error(
#                     #     parent, "Missing login credentials.", mode, theme_manager
#                     # )
#                     # error_frame.pack()
#                     # state["active_panel"] = error_frame
#                     # active_panels.append(error_frame)
#                     panel_choice["error_panel"].update_message("Missing login credentials")
#                     state["active_panel"] = panel_choice["error_panel"].pack()

#                 # No proxy request
#                 if use_proxy.lower() != "yes":
#                     # jql = "key = SCRUM-1"
#                     url = f"{server}rest/api/2/search?jql={options['jql']}"
#                     try:
#                         if options["jql"] != "Enter proper JQL query...":
#                             response = requests.get(url=url, headers=headers)

#                             # Return value
#                             results = response.json()
#                             configure_results(results, options, parent, state, panel_choice)
#                         else:
#                             raise Exception("Please provide proper jql query")
#                     except Exception as e:
#                         # error_frame = generate_error(
#                         #     parent, f"{e}", mode, theme_manager
#                         # )
#                         # error_frame.pack()
#                         # state["active_panel"] = error_frame
#                         # active_panels.append(error_frame)
#                         panel_choice["error_panel"].update_message("Missing login credentials")
#                         state["active_panel"] = panel_choice["error_panel"].pack()

#                 # Handles proxy requests
#                 if use_proxy.lower() != "no":
#                     if (
#                         http_proxy != ""
#                         and https_proxy != ""
#                         and use_proxy.lower() == "yes"
#                     ):
#                         proxy = {"http": http_proxy, "https": https_proxy}
#                         # DO REQUEST USING PROXY
#                         url = f"{server}rest/api/2/search?jql={options['jql']}"
#                         try:
#                             # if options["jql"] != "Enter proper JQL query...":
#                             response = requests.get(
#                                 url=url, headers=headers, proxies=proxy
#                             )

#                             # Return value
#                             results = response.json()
#                             configure_results(results, options, parent, state, mode)
#                             # else:
#                             #     raise Exception("Please provide proper jql query")
#                         except JIRAError as e:
#                             # error_frame = generate_error(
#                             #     parent, f"{e}", mode, theme_manager
#                             # )
#                             # error_frame.pack()
#                             # state["active_panel"] = error_frame
#                             # active_panels.append(error_frame)
#                             panel_choice["error_panel"].update_message("Missing login credentials")
#                             state["active_panel"] = panel_choice["error_panel"].pack()

#                     elif (
#                         use_proxy.lower() == "yes"
#                         and http_proxy == ""
#                         or https_proxy == ""
#                     ):
#                         # error_frame = generate_error(
#                         #     parent,
#                         #     "Must have values in both HTTP and HTTPS proxies in order to use.",
#                         #     mode,
#                         #     theme_manager,
#                         # )
#                         # error_frame.pack()
#                         # state["active_panel"] = error_frame
#                         # active_panels.append(error_frame)
#                         panel_choice["error_panel"].update_message("Missing login credentials")
#                         state["active_panel"] = panel_choice["error_panel"].pack()
#             else:
#                 # error_frame = generate_error(
#                 #     parent, "Missing Jira server url.", mode, theme_manager
#                 # )
#                 # error_frame.pack()
#                 # state["active_panel"] = error_frame
#                 # active_panels.append(error_frame)
#                 panel_choice["error_panel"].update_message("Missing login credentials")
#                 state["active_panel"] = panel_choice["error_panel"].pack()
#                 raise Exception
#         else:
#             print("No data")
#             # error_frame = generate_error(
#             #     parent,
#             #     "No Configuration Data found... please press Configure button at top left.",
#             #     mode,
#             #     theme_manager,
#             # )
#             # error_frame.pack(fill="both", padx=10)
#             # state["active_panel"] = error_frame
#             # active_panels.append(error_frame)
#             panel_choice["error_panel"].update_message("Missing login credentials")
#             state["active_panel"] = panel_choice["error_panel"].pack()
#     # print(f"{active_panels=}")

def switch_panel(panel_key, ui_state, panel_choice):
    print("PANEL SWITCH")
    current = ui_state.get("active_panel")
    if current:
        current.pack_forget()
    next_panel = panel_choice[panel_key]
    if panel_key == "error_panel":
        next_panel.pack(fill="x", padx=100, pady=10)
    if panel_key == "configure_panel":
        next_panel.pack(fill="both", expand=True, padx=10, pady=10)
    ui_state["active_panel"] = next_panel

def toolbar_action(root, payload, ui_state, mode, theme_manager, active_panels, panel_choice):
    if payload["type"] == "search_jiras":
        switch_panel("configure_panel", ui_state, panel_choice)
        config_data = load_data()
        # print(config_data)
        headers = None
        proxies = None
        # HANDLE FOR EMPTY SEARCH BAR
        if payload["jql"] == "Enter proper JQL query":
            panel_choice["error_panel"].update_message("Missing JQL Statement.")
            switch_panel("error_panel", ui_state, panel_choice)
            # print(ui_state["active_panel"])
            return

        if config_data.get("server") == "" or config_data.get("server") == "Provide base url":
            panel_choice["error_panel"].update_message("Missing Jira server, please provide information in the configuration panel.")
            switch_panel("error_panel", ui_state, panel_choice)
            return

        if config_data.get("auth_type") == "Basic Auth":
            if config_data.get("username") == "" or config_data.get("password") == "" or config_data.get("username") == "Enter username or email" or config_data.get("password") == "Enter password or token" :
                panel_choice["error_panel"].update_message("Missing Username or Password, please provide information in the configuration panel.")
                switch_panel("error_panel", ui_state, panel_choice)
                return 
            else:
                try:
                    headers = {
                        "Authorization": f"Basic {encode_basic_auth(config_data.get("username"), config_data.get("password"))}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                except JIRAError as e:
                    panel_choice["error_panel"].update_message(f"Failed to build headers using provided username/password.\nReason = {e}")
                    switch_panel("error_panel", ui_state, panel_choice)
                    return 
        elif config_data.get("auth_type") == "Token Auth":
            if config_data.get("token") == "" or config_data.get("token") == "(Bearer Token) JWT or OAuth 2.0 only":
                panel_choice["error_panel"].update_message("Missing Bearer Token, please provide information in the configuration panel.")
                switch_panel("error_panel", ui_state, panel_choice)
                return 
            else:
                try:
                    # jira = JIRA(server=server, token_auth=token)
                    headers = {
                        "Authorization": f"Bearer {config_data.get("token")}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                except JIRAError as e:
                    panel_choice["error_panel"].update_message(f"Failed to build headers using provided Bearer Token.\nReason = {e}")
                    switch_panel("error_panel", ui_state, panel_choice)
                    return 
                
        if config_data.get("proxy_option").lower() == "yes":
            # print("HERE")
            if config_data.get("http_proxy") == "" or config_data.get("https_proxy") == "":
                panel_choice["error_panel"].update_message(f"Missing proxy information, please provide information in the configuration panel.")
                switch_panel("error_panel", ui_state, panel_choice)
                return 
            else:
                proxies = {
                    "http": config_data.get("http_proxy"),
                    "https": config_data.get("https_proxy")
                }
                
        # LOGIC FOR PULLING TICKETS GOES HERE
        print(f"{headers=}\n{proxies=}")

    elif payload["type"] == "configure":
        switch_panel("configure_panel", ui_state, panel_choice)
