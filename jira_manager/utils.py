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
from jira_manager.sql_manager import (
    read_from_table,
    add_column_to_table,
    insert_into_table,
    run_sql_stmt,
    add_or_find_key_return_id,
    add_or_find_field_return_id,
)
from requests.exceptions import RequestException
from multiprocessing import Process, Queue, cpu_count
from time import sleep
from threading import Thread
from jira_manager.custom_panels import ErrorMessageBuilder, switch_panel

# def create_jira_card(parent, title, description, theme_manager, aspect_ratio=3.0, radius=20):
#     # Create a canvas to draw the rounded background
#     canvas = tk.Canvas(parent, highlightthickness=0)
#     canvas.config(width=300, height=100)  # Initial size
#     theme_manager.register(canvas, "frame")
#     # Create a frame to hold the content
#     content = tk.Frame(canvas)
#     theme_manager.register(content, "frame")
#     # Add title and description
#     title = tk.Label(
#         content,
#         text=title,
#         font=("Trebuchet MS", 12, "bold"),
#         anchor="center",
#         justify="center",
#     )
#     title.pack(pady=(5, 2))
#     theme_manager.register(title, "label")

#     description = tk.Label(
#         content, text=description, wraplength=280, justify="center"
#     )
#     description.pack(pady=(0, 5))
#     theme_manager.register(description, "label")

#     # Draw rounded rectangle on canvas
#     # def draw_rounded_rect(w, h):
#     #     canvas.delete("bg")
#     #     x1, y1, x2, y2 = 0, 0, w, h
#     #     r = radius
#     #     points = [
#     #         x1 + r,
#     #         y1,
#     #         x2 - r,
#     #         y1,
#     #         x2,
#     #         y1,
#     #         x2,
#     #         y1 + r,
#     #         x2,
#     #         y2 - r,
#     #         x2,
#     #         y2,
#     #         x2 - r,
#     #         y2,
#     #         x1 + r,
#     #         y2,
#     #         x1,
#     #         y2,
#     #         x1,
#     #         y2 - r,
#     #         x1,
#     #         y1 + r,
#     #         x1,
#     #         y1,
#     #     ]
#     #     canvas.create_polygon(
#     #         points, fill="black", outline="#ccc", smooth=True, tags="bg"
#     #     )

#     # Handle resizing and aspect ratio
#     def enforce_aspect(event):
#         width = event.width
#         height = int(width / aspect_ratio)
#         canvas.config(width=width, height=height)
#         # draw_rounded_rect(width, height)
#         canvas.coords("content", width // 2, height // 2)

#     # Bind resize event
#     canvas.bind("<Configure>", enforce_aspect)

#     # Place content in the center of the canvas
#     canvas.create_window(0, 0, window=content, anchor="center", tags="content")

#     return canvas

# def create_jira_card(parent, title, description, theme_manager, aspect_ratio=3.0, radius=20):
#     card_frame = tk.Frame(parent)
#     title = tk.Label(card_frame, text=title)
#     title.pack(padx=10, pady=10)
#     description = tk.Label(card_frame, text=description)
#     description.pack(padx=10, pady=10)
#     return card_frame

def create_jira_card(parent, title_text, description_text, theme_manager, on_click=None):
    card_frame = tk.Frame(parent, cursor="hand2", bd=2, relief="groove")
    theme_manager.register(card_frame, "frame")

    title = tk.Label(card_frame, text=title_text, font=("Segoe UI", 12, "bold"), anchor="w")
    title.pack(fill="x", padx=10, pady=(10, 5))
    theme_manager.register(title, "label")

    description = tk.Label(card_frame, text=description_text, wraplength=280, anchor="w")
    description.pack(fill="x", padx=10, pady=(0, 10))
    theme_manager.register(description, "label")

    if on_click:
        # Make entire frame clickable
        card_frame.bind("<Button-1>", lambda event: on_click())

        # Also make labels pass the event upward to frame
        for widget in (title, description):
            widget.bind("<Button-1>", lambda event: on_click())

    return card_frame


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, (str, list, tuple, dict, set)):
        return len(value) == 0
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value == 0
    return False  # Default: consider other types as non-empty


def batch_list(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]


def task_generator(queue):
    while queue:
        yield queue.pop(0)


def jira_task_handler(stop_flag, queue):
    while not stop_flag.is_set():
        print("Checking jira queue...")
        generator = task_generator(queue)
        try:
            task = next(generator)
        except StopIteration:
            pass
        sleep(1)
    print("Thread shutting down.")


# def update_ticket_bucket(ticket_bucket_items, panel_choice):
#     canvas = panel_choice["ticket_panel"].widget_registry.get("base_frame")  # this is your Canvas

#     # Clear previous canvas content
#     canvas.delete("all")

#     max_cols = 5
#     card_width = 180
#     card_height = 120
#     spacing_x = 10
#     spacing_y = 10

#     for index, item in enumerate(ticket_bucket_items):
#         row = index // max_cols
#         col = index % max_cols

#         x = col * (card_width + spacing_x)
#         y = row * (card_height + spacing_y)

#         card = create_jira_card(canvas, item[1], "Test Description")
#         canvas.create_window(x, y, window=card, anchor="nw", width=card_width, height=card_height)

#     # Update scrollable region
#     canvas.update_idletasks()
#     canvas.configure(scrollregion=canvas.bbox("all"))

#     # Rebind mousewheel scrolling
#     canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

def pull_jira_fields():
    print("hello!")

def update_ticket_bucket(ticket_bucket_items, panel_choice, theme_manager):
    base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")

    # Clear previous content
    for widget in base_frame.winfo_children():
        widget.destroy()

    max_cols = 5

    # Make columns expandable
    for col in range(max_cols):
        base_frame.columnconfigure(col, weight=1)

    for index, item in enumerate(ticket_bucket_items):
        row = index // max_cols
        col = index % max_cols

        card = create_jira_card(base_frame, item[1], "Test Description", theme_manager, pull_jira_fields)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")  # sticky makes the card stretch

# def core_handler(
#     stop_flag, queue, db_path, jira_queue, state, panel_choice, widget_registry
# ):
#     items = None
#     had_error = 0
#     buffer = 1
#     thread_count = cpu_count() - buffer

#     # SETUP TICKET BUCKET
#     ticket_bucket_items = run_sql_stmt(db_path, "SELECT * FROM tickets", stmt_type="select")
#     last_count = len(ticket_bucket_items)
#     update_ticket_bucket(ticket_bucket_items, panel_choice)

#     # RUN LOOP LOGIC
#     while not stop_flag.is_set():
#         # CHECK FOR UPDATE IN TICKET BUCKET
#         check_bucket_items = run_sql_stmt(db_path, "SELECT * FROM tickets", stmt_type="select")
#         check_len = len(check_bucket_items)
#         print(f"Last Count: {last_count}\nCheck Bucket Length: {len(check_bucket_items)}")
#         if check_len > last_count:
#             update_ticket_bucket(check_bucket_items, panel_choice)
#             last_count = check_len
def core_handler(
    stop_flag, queue, db_path, jira_queue, state, panel_choice, widget_registry, theme_manager
):
    items = None
    had_error = 0
    buffer = 1
    thread_count = cpu_count() - buffer

    def queue_ui_update(items):
        def _update():
            update_ticket_bucket(items, panel_choice, theme_manager)
        panel_choice["ticket_panel"].after(0, _update)

    # INITIAL DRAW
    ticket_bucket_items = run_sql_stmt(db_path, "SELECT * FROM tickets ORDER BY CAST(SUBSTR(key, INSTR(key, \"-\") + 1) AS INTEGER) DESC;", stmt_type="select")
    last_count = len(ticket_bucket_items)
    queue_ui_update(ticket_bucket_items)

    # BACKGROUND LOOP
    while not stop_flag.is_set():
        check_bucket_items = run_sql_stmt(db_path, "SELECT * FROM tickets ORDER BY CAST(SUBSTR(key, INSTR(key, \"-\") + 1) AS INTEGER) DESC;", stmt_type="select")
        check_len = len(check_bucket_items)
        print(f"Last Count: {last_count}\nCheck Bucket Length: {check_len}")

        if check_len > last_count:
            queue_ui_update(check_bucket_items)
            last_count = check_len

        config = load_data()
        print("Checking databse queue...")
        generator = task_generator(queue)
        try:
            task = next(generator)
            run_database_updates(
                task.get("db_path"),
                task.get("server"),
                task.get("headers"),
                task.get("ticket_list"),
            )
        except StopIteration:
            pass  # Nothing to do this round

        # CHECKING FOR TICKETS THAT NEED UPDATING ON JIRA SIDE
        try:
            tickets = run_sql_stmt(
                db_path,
                stmt_type="select",
                sql="SELECT * FROM tickets WHERE needs_update = ?",
                params=(1,)
            )
            for ticket in tickets:
                if ticket not in jira_queue:
                    jira_queue.append(ticket)
        except Exception:
            print("Error occurred grabbing tickets from database.")

        # MULTITHREAD PROCESS
        if len(jira_queue) > thread_count:
            update_list = batch_list(jira_queue, thread_count)
            threads = []
            for update in update_list:
                print(f"{update=}")
                # thread = Thread(target=jira_task_handler, args=())

        # SINGLE THREAD PROCESS
        elif len(jira_queue) < thread_count and len(jira_queue) > 0:
            for jira in jira_queue:
                ticket_id = jira[0]
                key = jira[1]
                update_status = jira[2]
                sql = "select * from fields where ticket_id = ?"
                params = (ticket_id,)
                field_info = run_sql_stmt(
                    db_path, sql=sql, params=params, stmt_type="select"
                )
                url = f"{config.get("server")}rest/api/2/issue/{key}"
                proxies = None
                headers = None

                # HANDLING OF NEEDED REQUEST DATA
                if config.get("auth_type") == "Basic Auth":
                    headers = {
                        "Authorization": f"Basic {encode_basic_auth(config.get("username"), config.get("password"))}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                elif config.get("auth_type") == "Token Auth":
                    headers = {
                        "Authorization": f"Bearer {config.get("token")}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                if config.get("proxy_option").lower() == "yes":
                    proxies = {
                        "http": config.get("http_proxy"),
                        "https": config.get("https_proxy"),
                    }

                try:
                    # if state["active_panel"] == panel_choice["error_panel"] and had_error > 0:
                    #     switch_panel("ticket_panel", state, panel_choice, widget_registry)
                    #     had_error = 0
                    jira_data = requests.get(url, headers=headers, proxies=proxies)
                    print(f"{jira_data.status_code=}")

                # except RequestException as e:
                #     # This fires if you're offline or the server is unreachable
                #     class ErrorHandle:
                #         def __init__(self, status_code):
                #             self.status_code = status_code
                    
                #     if state["active_panel"] != panel_choice["error_panel"] and state["active_panel"] != panel_choice["configure_panel"]:
                #         panel_choice["error_panel"].update_message(
                #             "You're offline or Jira can't be reached.\nPlease check your connection. You must be online for the background worker to process Jira requests."
                #         )
                #         switch_panel("error_panel", state, panel_choice, widget_registry)
                #     jira_data = ErrorHandle(status_code=500)
                #     had_error += 1
                except:
                    class ErrorHandle:
                        def __init__(self, status_code):
                            self.status_code = status_code

                    jira_data = ErrorHandle(status_code=404)
                    had_error += 1

                # WORK IN PROGRESS -- THIS WILL FIND WHAT FIELDS NEED TO BE UPDATED ON JIRA SERVER
                try:
                    if jira_data.status_code in [200, 204]:
                        if state["active_panel"] == panel_choice["error_panel"] and had_error > 0:
                            switch_panel("ticket_panel", state, panel_choice, widget_registry, db_path)
                            had_error = 0
                        print(f"{jira_data.status_code=}")
                        items = []
                        data = jira_data.json()
                        for field in data["fields"]:
                            value = data["fields"][field]
                            for check_field in field_info:
                                is_editable = check_field[6]
                                field_type = check_field[4]
                                field_name = check_field[3]
                                field_value = check_field[8]
                                if str(field_name).lower() == str(field).lower() and str(value).lower() != str(field_value).lower():
                                    print("Bool = ", is_empty(value), " - ", is_empty(field_value))
                                    if is_empty(value) and is_empty(field_value):
                                        print(f"{value=}\n{field_value=}")
                                        save_item = {"field": field_name, "value": field_value, "key": data["key"]}
                                        print(f"{save_item}")
                                        if save_item not in items:
                                            items.append(save_item)
                    else:
                        # if state["active_panel"] != panel_choice["error_panel"] and state["active_panel"] != panel_choice["configure_panel"]:
                        #     panel_choice["error_panel"].update_message(
                        #         "There was an error with the background worker.. please restart application or contact customer support."
                        #     )
                        #     switch_panel("error_panel", state, panel_choice, widget_registry)
                        # print(f"Error with job - {jira_queue[0]}")
                        print(f"Error occurred trying to update {jira_queue[0]}")
                    if items:
                        print(f"{items=}")         
                except Exception as e:
                    print(f"{e=}")

        sleep(1)
    print("Thread shutting down.")


def run_database_updates(db_path, server, headers, jira_tickets):
    print("Running database update")
    for ticket in jira_tickets:
        key = ticket["key"]
        ticket_id = add_or_find_key_return_id(db_path, key)
        editable_fields = get_editable_fields_v2(key, server, headers)
        mapped_fields = map_fields_for_db(editable_fields, ticket)
        for field in mapped_fields:
            fields_id = add_or_find_field_return_id(db_path, ticket_id, field)
            print(f"{fields_id=}")


def map_fields_for_db(editable_fields, current_issue_fields=None):
    """
    HOW TO USE:
    mapped_rows = map_fields_for_db(editable_fields, current_issue["fields"])
    insert_fields_into_db(sqlite_connection, ticket_id, mapped_rows)
    """
    field_rows = []
    for fid, fdata in editable_fields.items():
        schema = fdata.get("schema", {})
        ftype = schema.get("type", "string")
        custom = schema.get("custom")
        operations = fdata.get("operations", [])

        # Use your widget logic
        widget_map = {
            "string": "TextEntry",
            "text": "RichTextBox",
            "user": "UserPicker",
            "array": "MultiSelect",
            "number": "NumericEntry",
            "date": "DatePicker",
            "option": "Dropdown",
        }
        widget = widget_map.get(ftype, "TextEntry")
        if custom == "com.atlassian.jira.plugin.system.customfieldtypes:labels":
            widget = "TagInput"
        elif (
            custom
            == "com.atlassian.jira.plugin.system.customfieldtypes:multicheckboxes"
        ):
            widget = "CheckboxGroup"

        # Pull current value from live fields or leave empty
        current_value = ""
        if current_issue_fields:
            current_value = current_issue_fields["fields"].get(fid, "")

        # Prepare one row for each field
        row = {
            "field_key": fid,
            "field_name": fdata.get("name", fid),
            "field_type": ftype,
            "widget_type": widget,
            "is_editable": bool("set" in operations),
            "allowed_values": json.dumps(fdata.get("allowedValues", [])),
            "current_value": str(current_value),
        }
        field_rows.append(row)

    return field_rows


def get_editable_fields_v2(issue_key, base_url, headers):
    url = f"{base_url}/rest/api/2/issue/{issue_key}/editmeta"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("fields", {})


# def map_fields_to_widgets(editable_fields):
#     widget_map = {
#         "string": "text_input",
#         "text": "multiline_text",
#         "user": "user_picker",
#         "array": "multi_select",
#         "number": "numeric_input",
#         "date": "date_picker",
#         "option": "dropdown"
#     }

#     field_definitions = []
#     for field_id, field_data in editable_fields.items():
#         field_type = field_data["schema"].get("type", "string")
#         widget = widget_map.get(field_type, "text_input")
#         allowed_values = field_data.get("allowedValues", [])

#         field_definitions.append({
#             "id": field_id,
#             "name": field_data.get("name", field_id),
#             "type": field_type,
#             "widget": widget,
#             "allowed": allowed_values
#         })

#     return field_definitions


def map_fields_to_widgets(editable_fields, current_issue_fields=None):
    widget_map = {
        "string": "TextEntry",
        "text": "RichTextBox",
        "user": "UserPicker",
        "array": "MultiSelect",
        "number": "NumericEntry",
        "date": "DatePicker",
        "option": "Dropdown",
    }

    field_layout = []
    for fid, fdata in editable_fields.items():
        schema = fdata.get("schema", {})
        ftype = schema.get("type", "string")
        custom = schema.get("custom")
        widget = widget_map.get(ftype, "TextEntry")

        # Handle custom field types
        if custom == "com.atlassian.jira.plugin.system.customfieldtypes:labels":
            widget = "TagInput"
        elif (
            custom
            == "com.atlassian.jira.plugin.system.customfieldtypes:multicheckboxes"
        ):
            widget = "CheckboxGroup"

        # Get initial value from current_issue_fields or fallback to defaultValue or blank
        if current_issue_fields:
            value = current_issue_fields.get(fid, "")
        else:
            value = fdata.get("defaultValue", "")

        field_layout.append(
            {
                "id": fid,
                "name": fdata.get("name", fid),
                "widget": widget,
                "value": value,
                "allowed": fdata.get("allowedValues", []),
            }
        )

    return field_layout


# def grab_data_list(tickets) -> list:
#     excluded_fields = [
#         # System-managed or read-only
#         "statuscategorychangedate",
#         "created",
#         "updated",
#         "lastViewed",
#         "workratio",
#         "aggregateprogress",
#         "aggregatetimespent",
#         "aggregatetimeestimate",
#         "aggregatetimeoriginalestimate",
#         # "resolutiondate",
#         "votes",
#         "watches",
#         "progress",
#         # Permission-sensitive or restricted updates
#         "security",
#         # "creator",
#         # "reporter",
#         "statusCategory",
#         "project",
#         # "status",
#         "issuetype",
#         # Fields currently NoneType / unset
#         "timespent",
#         "timeoriginalestimate",
#         # "description",
#         "resolution",
#         # "customfield_10021",
#         # "customfield_10001",
#         # "customfield_10016",
#         # "customfield_10038",
#         "environment",
#         "timeestimate",
#         # "duedate",
#         "comment",  # Requires separate endpoint for updates
#         "worklog",  # Also updated via a dedicated endpoint
#         "attachment",  # Cannot be updated via issue PUT; use upload API
#         "customfield_*_readonly",  # Any custom fields that are read-only by config
#         "parent",  # Only relevant for sub-tasks; changing it moves the issue
#         "epic",  # Epic link field (varies by instance, often custom)
#         "sprint",  # Sprint field (Scrum boards); may be managed by board automation
#         "rank",
#     ]
#     ticket_data = {}
#     data_list = []
#     ticket_field_list = []
#     for ticket in tickets["issues"]:
#         ticket_data["key"] = ticket["key"]
#         for field in ticket["fields"]:
#             if "NoneType" not in str(type(ticket["fields"][field])):
#                 if field not in excluded_fields:
#                     ticket_field_list.append((field, type(ticket["fields"][field])))
#         ticket_data["fields_types"] = ticket_field_list
#         data_list.append(ticket_data)
#     return data_list


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
            theme = config.get("theme", "light")  # Default to light
            return theme.lower()
    except Exception:
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


# def create_jira_card(parent, title, description, aspect_ratio=3.0, radius=20):
#     # Create a canvas to draw the rounded background
#     canvas = tk.Canvas(parent, bg=parent["bg"], highlightthickness=0)
#     canvas.config(width=300, height=100)  # Initial size

#     # Create a frame to hold the content
#     content = tk.Frame(canvas, bg="white")

#     # Add title and description
#     tk.Label(
#         content,
#         text=title,
#         font=("Trebuchet MS", 12, "bold"),
#         bg="white",
#         anchor="center",
#         justify="center",
#     ).pack(pady=(5, 2))
#     tk.Label(
#         content, text=description, wraplength=280, justify="center", bg="white"
#     ).pack(pady=(0, 5))

#     # Draw rounded rectangle on canvas
#     def draw_rounded_rect(w, h):
#         canvas.delete("bg")
#         x1, y1, x2, y2 = 0, 0, w, h
#         r = radius
#         points = [
#             x1 + r,
#             y1,
#             x2 - r,
#             y1,
#             x2,
#             y1,
#             x2,
#             y1 + r,
#             x2,
#             y2 - r,
#             x2,
#             y2,
#             x2 - r,
#             y2,
#             x1 + r,
#             y2,
#             x1,
#             y2,
#             x1,
#             y2 - r,
#             x1,
#             y1 + r,
#             x1,
#             y1,
#         ]
#         canvas.create_polygon(
#             points, fill="white", outline="#ccc", smooth=True, tags="bg"
#         )

#     # Handle resizing and aspect ratio
#     def enforce_aspect(event):
#         width = event.width
#         height = int(width / aspect_ratio)
#         canvas.config(width=width, height=height)
#         draw_rounded_rect(width, height)
#         canvas.coords("content", width // 2, height // 2)

#     # Bind resize event
#     canvas.bind("<Configure>", enforce_aspect)

#     # Place content in the center of the canvas
#     canvas.create_window(0, 0, window=content, anchor="center", tags="content")

#     return canvas


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


def fetch_all_issues(config_data, payload, headers, proxies):
    base_url = f"{config_data.get('server')}rest/api/2/search"
    jql = payload["jql"]
    start_at = 0
    max_results = 100  # You can go up to 1000 depending on your Jira settings
    all_issues = []

    while True:
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results
        }

        response = requests.get(
            base_url,
            headers=headers,
            proxies=proxies,
            timeout=360,
            params=params
        )

        # 🚨 Error Handling (same logic as yours)
        if response.status_code not in [200, 204]:
            status = response.status_code
            message = response.text
            match status:
                case 400:
                    error_msg = "Bad Request – Please check your JQL query or input format."
                case 401:
                    error_msg = "Unauthorized – Your credentials might be missing or invalid."
                case 403:
                    error_msg = "Forbidden – You don’t have permission to access this Jira resource."
                case 404:
                    error_msg = "Not Found – The Jira endpoint or project wasn't located."
                case 500:
                    error_msg = "Jira Server Error – Something went wrong on their end."
                case _:
                    error_msg = f"Unexpected response.\nStatus Code: {status}\nMessage: {message}"
            raise Exception(error_msg)

        data = response.json()
        issues = data.get("issues", [])
        all_issues.extend(issues)

        if len(issues) < max_results:
            break  # No more pages

        start_at += max_results

    return all_issues

def toolbar_action(payload, ui_state, panel_choice, widget_registry, queue):

    jql_query = widget_registry.get("jql_query")
    db_path = "jira_manager/tickets.db"
    config_data = load_data()

    # LOGIC FOR JIRA SEARCH PANEL
    if payload["type"] == "search_jiras":
        headers = None
        proxies = None
        # HANDLE FOR EMPTY SEARCH BAR
        if payload["jql"] == "Enter proper JQL query":
            panel_choice["error_panel"].update_message("Missing JQL Statement.")
            switch_panel("error_panel", ui_state, panel_choice, widget_registry)
            return

        if (
            config_data.get("server") == ""
            or config_data.get("server") == "Provide base url"
        ):
            panel_choice["error_panel"].update_message(
                "Missing Jira server, please provide information in the configuration panel."
            )
            switch_panel("error_panel", ui_state, panel_choice, widget_registry)
            return

        if config_data.get("auth_type") == "Basic Auth":
            if (
                config_data.get("username") == ""
                or config_data.get("password") == ""
                or config_data.get("username") == "Enter username or email"
                or config_data.get("password") == "Enter password or token"
            ):
                panel_choice["error_panel"].update_message(
                    "Missing Username or Password, please provide information in the configuration panel."
                )
                switch_panel("error_panel", ui_state, panel_choice, widget_registry)
                return
            else:
                try:
                    headers = {
                        "Authorization": f"Basic {encode_basic_auth(config_data.get("username"), config_data.get("password"))}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                except JIRAError as e:
                    panel_choice["error_panel"].update_message(
                        f"Failed to build headers using provided username/password.\nReason = {e}"
                    )
                    switch_panel("error_panel", ui_state, panel_choice, widget_registry)
                    return
        elif config_data.get("auth_type") == "Token Auth":
            if (
                config_data.get("token") == ""
                or config_data.get("token") == "(Bearer Token) JWT or OAuth 2.0 only"
            ):
                panel_choice["error_panel"].update_message(
                    "Missing Bearer Token, please provide information in the configuration panel."
                )
                switch_panel("error_panel", ui_state, panel_choice, widget_registry)
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
                    panel_choice["error_panel"].update_message(
                        f"Failed to build headers using provided Bearer Token.\nReason = {e}"
                    )
                    switch_panel("error_panel", ui_state, panel_choice, widget_registry)
                    return

        if config_data.get("proxy_option").lower() == "yes":
            if (
                config_data.get("http_proxy") == ""
                or config_data.get("https_proxy") == ""
            ):
                panel_choice["error_panel"].update_message(
                    f"Missing proxy information, please provide information in the configuration panel."
                )
                switch_panel("error_panel", ui_state, panel_choice, widget_registry)
                return
            else:
                proxies = {
                    "http": config_data.get("http_proxy"),
                    "https": config_data.get("https_proxy"),
                }

        # LOGIC FOR PULLING TICKETS GOES HERE
        try:
            # JQL SEARCH FUNCTIONALITY
            tickets = fetch_all_issues(config_data, payload, headers, proxies)

            # SETS UP JOB QUEUES
            queue_data = {
                "db_path": db_path,
                "server": config_data.get("server"),
                "headers": headers,
                "ticket_list": tickets,
            }
            queue.append(queue_data)

            # PANEL SWITCH TO BUCKET
            switch_panel("ticket_panel", ui_state, panel_choice, widget_registry, db_path)

        except RequestException as e:
            # This fires if you're offline or the server is unreachable
            panel_choice["error_panel"].update_message(
                "You're offline or Jira can't be reached.\nPlease check your connection."
            )
            switch_panel("error_panel", ui_state, panel_choice, widget_registry)
        except Exception as e:
            panel_choice["error_panel"].update_message(
                f"There was an issue with the request to Jira.\nReason = {e}"
            )
            switch_panel("error_panel", ui_state, panel_choice, widget_registry)

    # LOGIC FOR CONFIGURE PANEL
    elif payload["type"] == "configure":

        switch_panel("configure_panel", ui_state, panel_choice, widget_registry)

    # LOGIC FOR TICKETS PANEL
    elif payload["type"] == "tickets":

        if (
            config_data.get("server") == ""
            or config_data.get("server") == "Provide base url"
        ):
            panel_choice["error_panel"].update_message(
                "Missing Jira server, please provide information in the configuration panel."
            )
            switch_panel("error_panel", ui_state, panel_choice, widget_registry)
            return

        if config_data.get("auth_type") == "Basic Auth":
            if (
                config_data.get("username") == ""
                or config_data.get("password") == ""
                or config_data.get("username") == "Enter username or email"
                or config_data.get("password") == "Enter password or token"
            ):
                panel_choice["error_panel"].update_message(
                    "Missing Username or Password, please provide information in the configuration panel."
                )
                switch_panel("error_panel", ui_state, panel_choice, widget_registry)
                return
        elif config_data.get("auth_type") == "Token Auth":
            if (
                config_data.get("token") == ""
                or config_data.get("token") == "(Bearer Token) JWT or OAuth 2.0 only"
            ):
                panel_choice["error_panel"].update_message(
                    "Missing Bearer Token, please provide information in the configuration panel."
                )
                switch_panel("error_panel", ui_state, panel_choice, widget_registry)
                return

        if config_data.get("proxy_option").lower() == "yes":
            if (
                config_data.get("http_proxy") == ""
                or config_data.get("https_proxy") == ""
            ):
                panel_choice["error_panel"].update_message(
                    f"Missing proxy information, please provide information in the configuration panel."
                )
                switch_panel("error_panel", ui_state, panel_choice, widget_registry)
                return

        # CHANGE BUCKET FOR DATABASE INFO
        try:
            ticket_data = run_sql_stmt(db_path, "select * from tickets", stmt_type="select")
        except:
            ticket_data = []
        if ticket_data != []:
            switch_panel("ticket_panel", ui_state, panel_choice, widget_registry, db_path)
        else:
            panel_choice["error_panel"].update_message(
                "No tickets have been loaded in, please configure a project or search using JQL query."
            )
            switch_panel("error_panel", ui_state, panel_choice, widget_registry)

    jql_query.reset_to_placeholder()
