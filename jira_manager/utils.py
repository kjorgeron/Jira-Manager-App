import tkinter as tk
import json
import requests
import base64
from jira import JIRAError
from jira_manager.custom_widgets import TicketCard
from pprint import pprint
from PIL import Image, ImageTk
from jira_manager.file_manager import load_data
from jira_manager.sql_manager import (
    run_sql_stmt,
    add_or_find_key_return_id,
    add_or_find_field_return_id,
    batch_insert_tickets
)
from requests.exceptions import RequestException
from multiprocessing import Queue
from time import sleep
from threading import Thread, Lock
from jira_manager.custom_panels import switch_panel, ErrorMessageBuilder

def run_error(panel_choice, ui_state, widget_registry, message):
    # ErrorMessageBuilder(
    #     master=root,
    #     theme_manager=theme_manager,
    #     message=message,
    # )
    # canvas._bind_mousewheel()
    panel_choice["error_panel"].update_message(
       message
    )
    switch_panel("error_panel", ui_state, panel_choice, widget_registry)
    return

def safe_button_action(button, action, delay=100, panel_choice=None):

    if button is not None:
        button.config(state="disabled")

    def run_and_enable():
        action()
        if button is not None:
            button.config(state="normal")

    # If button is not None, use after; else, just call action immediately
    if button is not None:
        button.after(delay, run_and_enable)
    else:
        action()
    


def batch_list(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]


def task_generator(queue):
    while queue:
        yield queue.pop(0)


def configure_handler(ui_state, panel_choice, widget_registry):
    while True:
        switch_panel("configure_panel", ui_state, panel_choice, widget_registry)
        break


def jql_search_handler(
    stop_flag,
    queue,
    panel_choice,
    theme_manager,
    card_retainer,
    db_path,
    selected_items,
    ui_state=None,
    widget_registry=None,
):
    print(f"{card_retainer=}")
    while not stop_flag.is_set():
        print("Running thread...")
        generator = task_generator(queue)
        try:
            task = next(generator)
            t_type = task.get("type")

            # HANDLE JQL SEARCH
            if t_type == "jql_search":
                print(f"{task.get("type")=}")
                config_data = task.get("config_data")
                payload = task.get("payload")
                headers = task.get("headers")
                proxies = task.get("proxies")
                thread_count = task.get("thread_count")
                run_count = task.get("run_count")

                try:
                    issues = fetch_all_issues_threaded(
                        config_data, payload, headers, proxies, thread_count
                    )
                    print(f"{len(issues)=}")

                    for issue in issues[:]:
                        check = {"key": issue["key"]}
                        if check in card_retainer:
                            print(f"HERE!!! {issue["key"]}")
                            issues.remove(issue)
                        else:
                            card_retainer.append({"key": issue["key"]})

                    threads = []
                    for batch in batch_list(issues, thread_count):
                        thread = Thread(
                            target=batch_insert_tickets,
                            args=(db_path, batch),
                            daemon=True,
                        )
                        threads.append(thread)
                        threads[-1].start()
                    for thread in threads:
                        thread.join()
                    print("Batch insert completed.")
                    # update_ticket_bucket(
                    #     card_retainer, panel_choice, theme_manager, db_path, selected_items)
                    switch_panel(
                        "ticket_panel",ui_state, panel_choice, widget_registry, db_path, theme_manager, card_retainer, selected_items)
                except requests.exceptions.HTTPError as err:
                    print(err)
                    # ErrorPopupBuilder(
                    #     master=panel_choice["ticket_panel"].master,
                    #     theme_manager=theme_manager,
                    #     message=f"There was an issue with the request to Jira.\nReason = {err}",
                    # )
                    run_error(panel_choice, ui_state, widget_registry, f"There was an issue with the request to Jira.\nReason = {err}")

            run_count["count"] = run_count["count"] - 1

        except StopIteration:

            break
    print("Thread shutting down.")


def update_ticket_bucket(
    ticket_bucket_items, panel_choice, theme_manager, db_path, selected_items
):

    base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")
    canvas = panel_choice["ticket_panel"].widget_registry.get("canvas")
    max_cols = 5

    # Make columns expandable
    for col in range(max_cols):
        base_frame.columnconfigure(col, weight=1)

    for index, item in enumerate(ticket_bucket_items):
        row = index // max_cols
        col = index % max_cols
        print(f"{item=}")
        update_ticket_bucket_with_single(
            item, panel_choice, theme_manager, db_path, selected_items
        )

    # Always update scrollregion after adding/removing cards
    base_frame.update_idletasks()
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))



def update_ticket_bucket_with_single(
    ticket, panel_choice, theme_manager, db_path, selected_items
):
    base_frame = panel_choice["ticket_panel"].widget_registry.get("base_frame")

    card = TicketCard(ticket, theme_manager, master=base_frame)
    if ticket["key"] in selected_items:
        card.set_bg(theme_manager.theme["pending_color"])
        card.widget_registry.get("select_btn").config(
            text="Unselect", bg=theme_manager.theme["pending_color"]
        )
    print(f"{ticket=}")
    children = base_frame.winfo_children()
    if children and children[0].winfo_ismapped():
        card.pack(side="top", fill="x", padx=5, pady=3, before=children[0])
    else:
        card.pack(side="top", fill="x", padx=5, pady=3)


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


def initialize_window():
    root = tk.Tk()
    root.title("TicketSmith")
    root.state("zoomed")
    # root.geometry("800x800")
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


def create_divider(parent, theme_manager):
    # --- Divider (optional) ---
    divider = tk.Frame(parent)
    divider.pack(fill=tk.X, padx=10)
    theme_manager.register(divider, "divider")


def encode_basic_auth(username: str, password: str) -> str:
    credentials = f"{username}:{password}"
    token_bytes = credentials.encode("utf-8")
    base64_token = base64.b64encode(token_bytes).decode("utf-8")
    return base64_token


def create_toolbar(parent, bg="#4C30EB", padding=10):
    toolbar = tk.Frame(parent, bg=bg, pady=padding)
    toolbar.pack(fill="x", padx=padding, pady=(padding, 0))
    return toolbar


def fetch_all_issues_threaded(
    config_data, payload, headers, proxies, thread_count=4, return_queue: Queue = None
):
    base_url = f"{config_data.get('server')}rest/api/2/search"
    jql = payload["jql"]
    max_results = 100

    # First, make an initial request to determine total
    response = requests.get(
        base_url,
        headers=headers,
        proxies=proxies,
        timeout=360,
        params={"jql": jql, "startAt": 0, "maxResults": 1},  # just get metadata
    )
    response.raise_for_status()
    total_issues = response.json().get("total", 0)

    issue_lock = Lock()
    all_issues = []

    def worker(start_at):
        params = {"jql": jql, "startAt": start_at, "maxResults": max_results}
        res = requests.get(
            base_url, headers=headers, proxies=proxies, timeout=360, params=params
        )

        if res.status_code not in [200, 204]:
            print(f"⚠️ Thread failed: {start_at} → {res.status_code}")
            return  # optional: raise or retry

        data = res.json()
        issues = data.get("issues", [])

        with issue_lock:
            all_issues.extend(issues)

    threads = []
    for start in range(0, total_issues, max_results):
        t = Thread(target=worker, args=(start,))
        threads.append(t)

    # Start batches of threads
    for i in range(0, len(threads), thread_count):
        batch = threads[i : i + thread_count]
        for t in batch:
            t.start()
        for t in batch:
            t.join()

    if return_queue == None:
        return all_issues
    else:
        return_queue.put(all_issues)


def configure_project_credentials(
    config_data, panel_choice, ui_state, widget_registry, root=None, theme_manager=None
):

    headers = None
    proxies = None

    if (
        config_data.get("server") == ""
        or config_data.get("server") == "Provide base url"
    ):
        # ErrorPopupBuilder(
        #     master=root,
        #     theme_manager=theme_manager,
        #     message="Missing Jira server, please provide information in the configuration panel.",
        # )
        run_error(panel_choice, ui_state, widget_registry, "Missing Jira server, please provide information in the configuration panel.")
        return

    if config_data.get("auth_type") == "Basic Auth":
        if (
            config_data.get("username") == ""
            or config_data.get("password") == ""
            or config_data.get("username") == "Enter username or email"
            or config_data.get("password") == "Enter password or token"
        ):
            # ErrorPopupBuilder(
            #     master=root,
            #     theme_manager=theme_manager,
            #     message="Missing Username or Password, please provide information in the configuration panel.",
            # )
            run_error(panel_choice, ui_state, widget_registry, "Missing Username or Password, please provide information in the configuration panel.")
            return
        else:
            try:
                headers = {
                    "Authorization": f"Basic {encode_basic_auth(config_data.get("username"), config_data.get("password"))}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            except JIRAError as e:
                # ErrorPopupBuilder(
                #     master=root,
                #     theme_manager=theme_manager,
                #     message=f"Failed to build headers using provided username/password.\nReason = {e}",
                # )
                run_error(panel_choice, ui_state, widget_registry, f"Failed to build headers using provided username/password.\nReason = {e}")
                return
    elif config_data.get("auth_type") == "Token Auth":
        if (
            config_data.get("token") == ""
            or config_data.get("token") == "(Bearer Token) JWT or OAuth 2.0 only"
        ):
            # ErrorPopupBuilder(
            #     master=root,
            #     theme_manager=theme_manager,
            #     message="Missing Bearer Token, please provide information in the configuration panel.",
            # )
            run_error(panel_choice, ui_state, widget_registry, "Missing Bearer Token, please provide information in the configuration panel.")
            return
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {config_data.get("token")}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            except JIRAError as e:
                # ErrorPopupBuilder(
                #     master=root,
                #     theme_manager=theme_manager,
                #     message=f"Failed to build headers using provided Bearer Token.\nReason = {e}",
                # )
                run_error(panel_choice, ui_state, widget_registry, f"Failed to build headers using provided Bearer Token.\nReason = {e}")
                return

    if config_data.get("proxy_option").lower() == "yes":
        if config_data.get("http_proxy") == "" or config_data.get("https_proxy") == "":
            ErrorMessageBuilder(
                master=root,
                theme_manager=theme_manager,
                message=f"Missing proxy information, please provide information in the configuration panel.",
            )
            return
        else:
            proxies = {
                "http": config_data.get("http_proxy"),
                "https": config_data.get("https_proxy"),
            }

    return (headers, proxies)


def toolbar_action(
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
    root=None,
):

    jql_query = widget_registry.get("jql_query")
    db_path = "jira_manager/tickets.db"
    config_data = load_data()
    print(run_count)

    headers, proxies = configure_project_credentials(
        config_data, panel_choice, ui_state, widget_registry, root, theme_manager
    )

    # LOGIC FOR JIRA SEARCH PANEL
    if payload["type"] == "search_jiras":
        panel_choice["ticket_panel"].widget_registry.get("canvas").yview_moveto(0)
        # I NEED TO CHANGE THIS TO BE A QUEUE SO THE USER CAN QUEUE AS MANY AS WANTED BUT IT DOES EACH JOB 1 AT A TIME IN BACKGROUND
        if run_count["count"] > thread_count:
            # ErrorPopupBuilder(
            #     master=root,
            #     theme_manager=theme_manager,
            #     message="You have exceeded your limit of threads. Please let current tasks finish.",
            # )
            run_error(panel_choice, ui_state, widget_registry, "You have exceeded your limit of threads. Please let current tasks finish.")
            return

        # HANDLE FOR EMPTY SEARCH BAR
        if payload["jql"] == "Enter proper JQL query":
            # ErrorPopupBuilder(
            #     master=root,
            #     theme_manager=theme_manager,
            #     message="Missing JQL Statement.",
            # )
            run_error(panel_choice, ui_state, widget_registry, "Missing JQL Statement.")
            return
        
        try:
            print("Running JQL search...")
            # JQL SEARCH FUNCTIONALITY
            # switch_panel(
            #     "ticket_panel",
            #     ui_state,
            #     panel_choice,
            #     widget_registry,
            #     db_path,
            #     theme_manager,
            #     card_retainer,
            # )
            try:
                run_count["count"] += 1
                task = {
                    "type": "jql_search",
                    "config_data": config_data,
                    "payload": payload,
                    "headers": headers,
                    "proxies": proxies,
                    "thread_count": thread_count,
                    "run_count": run_count,
                }
                thread = Thread(
                    target=jql_search_handler,
                    args=(
                        stop_flag,
                        [task],
                        panel_choice,
                        theme_manager,
                        card_retainer,
                        db_path,
                        selected_items,
                        ui_state,
                        widget_registry
                    ),
                )
                thread.start()
            except Exception as e:
                # ErrorPopupBuilder(
                #     master=root,
                #     theme_manager=theme_manager,
                #     message=f"There was an error with the jql request thread handler.\nReason = {e}.",
                # )
                run_error(panel_choice, ui_state, widget_registry, f"There was an error with the jql request thread handler.\nReason = {e}.")
                return
        except RequestException as e:
            # ErrorPopupBuilder(
            #     master=root,
            #     theme_manager=theme_manager,
            #     message="You're offline or Jira can't be reached.\nPlease check your connection.",
            # )
            run_error(panel_choice, ui_state, widget_registry, "You're offline or Jira can't be reached.\nPlease check your connection.")
            return
        except Exception as e:
            # ErrorPopupBuilder(
            #     master=root,
            #     theme_manager=theme_manager,
            #     message=f"There was an issue with the request to Jira.\nReason = {e}",
            # )
            run_error(panel_choice, ui_state, widget_registry, f"There was an issue with the request to Jira.\nReason = {e}")
            return

    # LOGIC FOR CONFIGURE PANEL
    elif payload["type"] == "configure":
        thread = Thread(
            target=configure_handler,
            args=(ui_state, panel_choice, widget_registry),
        )
        thread.start()


    # LOGIC FOR TICKETS PANEL
    elif payload["type"] == "tickets":
        tickets = run_sql_stmt(db_path, "SELECT * FROM tickets", stmt_type="select")
        if not tickets:
            panel_choice["error_panel"].update_message(
                "No tickets stored in local database.\nPlease configure your Jira connection and fetch tickets."
            )
            switch_panel("error_panel", ui_state, panel_choice, widget_registry)
        else:
            # Sort card_retainer by integer part after dash, DESC
            def ticket_key_int(ticket):
                key = ticket.get("key", "")
                try:
                    return int(key.split("-")[-1])
                except Exception:
                    return 0
            card_retainer.sort(key=ticket_key_int, reverse=True)
            switch_panel(
                "ticket_panel",
                ui_state,
                panel_choice,
                widget_registry,
                db_path,
                theme_manager,
                card_retainer,
                selected_items,
            )

    jql_query.reset_to_placeholder()
