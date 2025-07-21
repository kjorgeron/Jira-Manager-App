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
from jira_manager.sql_manager import read_from_table
from requests.exceptions import RequestException



def grab_fields_and_type(tickets) -> list[tuple]:
    ticket_field_list = []
    for ticket in tickets["issues"]:
        for field in ticket["fields"]:
            ticket_field_list.append((field, type(ticket["fields"][field])))
    return ticket_field_list


def initialize_window():
    root = tk.Tk()
    root.title("TicketSmith")
    root.geometry("800x800")
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
        "Entry",
        "TEntry",
        "TCombobox",
        "Text",
        "Custom.TCombobox",
        "Listbox",
        "Button",
        "Checkbutton",
        "Radiobutton",
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


def configure_results(
    results, options, parent, state, mode, theme_manager, panel_choice
):
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

        scroll_area = create_scrollable_frame(parent)
        scroll_area.pack(fill="both", padx=10, expand=True)

        panel_choice["error_panel"].update_message("Missing login credentials")
        state["active_panel"] = panel_choice["error_panel"].pack()


def switch_panel(panel_key, ui_state, panel_choice):
    print(f"PANEL SWITCH -> {panel_key}")
    current = ui_state.get("active_panel")
    if current:
        current.pack_forget()
    next_panel = panel_choice[panel_key]
    if panel_key == "error_panel":
        next_panel.pack(fill="x", padx=100, pady=10)
    if panel_key == "configure_panel":
        next_panel.pack(fill="both", expand=True, padx=10, pady=10)
    if panel_key == "ticket_panel":
        next_panel.pack(fill="both", expand=True, padx=10, pady=10)
    ui_state["active_panel"] = next_panel


def toolbar_action(payload, ui_state, panel_choice, widget_registry):

    widget = widget_registry.get("welcome_label")
    jql_query = widget_registry.get("jql_query")

    # LOGIC FOR JIRA SEARCH PANEL
    if payload["type"] == "search_jiras":
        # switch_panel("configure_panel", ui_state, panel_choice)
        config_data = load_data()
        # print(config_data)
        headers = None
        proxies = None
        # HANDLE FOR EMPTY SEARCH BAR
        if payload["jql"] == "Enter proper JQL query":
            widget.pack_forget()
            # widget.config(text="Oops!!! A failure has occurred.")
            panel_choice["error_panel"].update_message("Missing JQL Statement.")
            switch_panel("error_panel", ui_state, panel_choice)
            return

        if (
            config_data.get("server") == ""
            or config_data.get("server") == "Provide base url"
        ):
            widget.pack_forget()
            # widget.config(text="Oops!!! A failure has occurred.")
            panel_choice["error_panel"].update_message(
                "Missing Jira server, please provide information in the configuration panel."
            )
            switch_panel("error_panel", ui_state, panel_choice)
            return

        if config_data.get("auth_type") == "Basic Auth":
            if (
                config_data.get("username") == ""
                or config_data.get("password") == ""
                or config_data.get("username") == "Enter username or email"
                or config_data.get("password") == "Enter password or token"
            ):
                widget.pack_forget()
                # widget.config(text="Oops!!! A failure has occurred.")
                panel_choice["error_panel"].update_message(
                    "Missing Username or Password, please provide information in the configuration panel."
                )
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
                    widget.pack_forget()
                    # widget.config(text="Oops!!! A failure has occurred.")
                    panel_choice["error_panel"].update_message(
                        f"Failed to build headers using provided username/password.\nReason = {e}"
                    )
                    switch_panel("error_panel", ui_state, panel_choice)
                    return
        elif config_data.get("auth_type") == "Token Auth":
            if (
                config_data.get("token") == ""
                or config_data.get("token") == "(Bearer Token) JWT or OAuth 2.0 only"
            ):
                widget.pack_forget()
                # widget.config(text="Oops!!! A failure has occurred.")
                panel_choice["error_panel"].update_message(
                    "Missing Bearer Token, please provide information in the configuration panel."
                )
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
                    widget.pack_forget()
                    # widget.config(text="Oops!!! A failure has occurred.")
                    panel_choice["error_panel"].update_message(
                        f"Failed to build headers using provided Bearer Token.\nReason = {e}"
                    )
                    switch_panel("error_panel", ui_state, panel_choice)
                    return

        if config_data.get("proxy_option").lower() == "yes":
            # print("HERE")
            if (
                config_data.get("http_proxy") == ""
                or config_data.get("https_proxy") == ""
            ):
                widget.pack_forget()
                # widget.config(text="Oops!!! A failure has occurred.")
                panel_choice["error_panel"].update_message(
                    f"Missing proxy information, please provide information in the configuration panel."
                )
                switch_panel("error_panel", ui_state, panel_choice)
                return
            else:
                proxies = {
                    "http": config_data.get("http_proxy"),
                    "https": config_data.get("https_proxy"),
                }

        # LOGIC FOR PULLING TICKETS GOES HERE
        print(f"{headers=}\n{proxies=}")
        try:
            url = f"{config_data.get('server')}rest/api/2/search?jql={payload['jql']}"
            response = requests.get(url, headers=headers, proxies=proxies, timeout=360)
            if response.status_code not in [200, 204]:
                status = response.status_code
                message = response.text

                if status == 400:
                    error_msg = "Bad Request – Please check your JQL query or input format."
                elif status == 401:
                    error_msg = "Unauthorized – Your credentials might be missing or invalid."
                elif status == 403:
                    error_msg = "Forbidden – You don’t have permission to access this Jira resource."
                elif status == 404:
                    error_msg = "Not Found – The Jira endpoint or project wasn't located."
                elif status == 500:
                    error_msg = "Jira Server Error – Something went wrong on their end."
                else:
                    error_msg = f"Unexpected response.\nStatus Code: {status}\nMessage: {message}"

                raise Exception(error_msg)

            else:
                # NEED TO HANDLE DATABASE STORAGE HERE
                print(response.status_code)
                tickets = response.json()
                fields_types_list = grab_fields_and_type(tickets)
                for item in fields_types_list:
                    field, typ = item
                    print(f"{field=}\n{typ=}")


                try:
                    ticket_data = read_from_table("jira_manager/tickets.db", "Tickets")
                    print(ticket_data)
                except:
                    ticket_data = [1]
                # CHANGE BUCKET FOR DATABASE INFO <-- THIS WILL INSTEAD NEED TO BE A LOAD SCREEN OF TICKETS GOING INTO THE BUCKET
                if ticket_data != []:
                    widget.config(text="Ticket Bucket")
                    widget.pack(fill="x", padx=10, pady=10)
                    switch_panel("ticket_panel", ui_state, panel_choice)
                else:
                    widget.pack_forget()
                    # widget.config(text="Oops!!! A failure has occurred.")
                    panel_choice["error_panel"].update_message(
                        "No tickets have been loaded in, please configure a project or search using JQL query."
                    )
                    switch_panel("error_panel", ui_state, panel_choice)
        except RequestException as e:
            # This fires if you're offline or the server is unreachable
            widget.pack_forget()
            panel_choice["error_panel"].update_message(
                "You're offline or Jira can't be reached.\nPlease check your connection."
            )
            switch_panel("error_panel", ui_state, panel_choice)
        except Exception as e:
            widget.pack_forget()
            # widget.config(text="Oops!!! A failure has occurred.")
            panel_choice["error_panel"].update_message(
                f"There was an issue with the request to Jira.\nReason = {e}"
            )
            switch_panel("error_panel", ui_state, panel_choice)


        # try:
        #     ticket_data = read_from_table("jira_manager/tickets.db", "Tickets")
        #     print(ticket_data)
        # except:
        #     ticket_data = [1]
        # # CHANGE BUCKET FOR DATABASE INFO <-- THIS WILL INSTEAD NEED TO BE A LOAD SCREEN OF TICKETS GOING INTO THE BUCKET
        # if ticket_data != []:
        #     widget.config(text="Ticket Bucket")
        #     widget.pack(fill="x", padx=10, pady=10)
        #     switch_panel("ticket_panel", ui_state, panel_choice)
        # else:
        #     widget.pack_forget()
        #     # widget.config(text="Oops!!! A failure has occurred.")
        #     panel_choice["error_panel"].update_message(
        #         "No tickets have been loaded in, please configure a project or search using JQL query."
        #     )
        #     switch_panel("error_panel", ui_state, panel_choice)

    # LOGIC FOR CONFIGURE PANEL
    elif payload["type"] == "configure":
        widget.pack_forget()
        switch_panel("configure_panel", ui_state, panel_choice)
        # widget.config(text="Lets configure your setup!")

    # LOGIC FOR TICKETS PANEL
    elif payload["type"] == "tickets":
        # CHANGE BUCKET FOR DATABASE INFO
        try:
            ticket_data = read_from_table("jira_manager/tickets.db", "Tickets")
            print(ticket_data)
        except:
            ticket_data = []
        if ticket_data != []:
            widget.config(text="Ticket Bucket")
            widget.pack(fill="x", padx=10, pady=10)
            switch_panel("ticket_panel", ui_state, panel_choice)
        else:
            widget.pack_forget()
            # widget.config(text="Oops!!! A failure has occurred.")
            panel_choice["error_panel"].update_message(
                "No tickets have been loaded in, please configure a project or search using JQL query."
            )
            switch_panel("error_panel", ui_state, panel_choice)

    jql_query.reset_to_placeholder()
