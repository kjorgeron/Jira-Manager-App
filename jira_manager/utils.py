import tkinter as tk
import json
import requests
import base64
from jira import JIRAError
from jira_manager.custom_widgets import TicketCard, WorkReceiptsPanel
from pprint import pprint
from PIL import Image, ImageTk
from jira_manager.file_manager import load_data
from jira_manager.sql_manager import (
    run_sql_stmt,
    add_or_find_key_return_id,
    add_or_find_field_return_id,
    batch_insert_tickets,
)
from requests.exceptions import RequestException
from queue import Queue, Empty
from threading import Thread, Lock
from jira_manager.custom_panels import (
    switch_panel,
    ErrorMessageBuilder,
    ErrorPopupBuilder,
)


def jql_worker(
    panel_choice,
    theme_manager,
    card_retainer,
    db_path,
    selected_items,
    ui_state,
    widget_registry,
    stop_flag,
    jql_task_queue,
    worker_state=None,
):
    if worker_state is not None:
        worker_state["running"] = True
    try:
        while not stop_flag.is_set():
            try:
                task = jql_task_queue.get(timeout=1)
            except Empty:
                break
            try:
                jql_search_handler(
                    stop_flag,
                    task,
                    panel_choice,
                    theme_manager,
                    card_retainer,
                    db_path,
                    selected_items,
                    ui_state,
                    widget_registry,
                )
            except Exception as e:
                print(f"Error in JQL worker: {e}")
            finally:
                jql_task_queue.task_done()
    finally:
        if worker_state is not None:
            worker_state["running"] = False
        print("JQL worker thread finished.")


def run_error(
    panel_choice=None,
    ui_state=None,
    widget_registry=None,
    message=None,
    theme_manager=None,
    root=None,
):
    if panel_choice:
        panel_choice["error_panel"].update_message(message)
        # Pass card_retainer and selected_items if available
        card_retainer = (
            panel_choice.get("card_retainer")
            if panel_choice and hasattr(panel_choice, "get")
            else None
        )
        selected_items = (
            panel_choice.get("selected_items")
            if panel_choice and hasattr(panel_choice, "get")
            else None
        )
        switch_panel(
            "error_panel",
            ui_state,
            panel_choice,
            widget_registry,
            None,
            None,
            card_retainer,
            selected_items,
        )
    else:
        ErrorPopupBuilder(
            master=root,
            theme_manager=theme_manager,
            message=message,
        )
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


def configure_handler(ui_state, panel_choice, widget_registry):
    while True:
        card_retainer = (
            panel_choice.get("card_retainer")
            if panel_choice and hasattr(panel_choice, "get")
            else None
        )
        selected_items = (
            panel_choice.get("selected_items")
            if panel_choice and hasattr(panel_choice, "get")
            else None
        )
        switch_panel(
            "configure_panel",
            ui_state,
            panel_choice,
            widget_registry,
            None,
            None,
            card_retainer,
            selected_items,
        )
        break


def jql_search_handler(
    stop_flag,
    task,
    panel_choice,
    theme_manager,
    card_retainer,
    db_path,
    selected_items,
    ui_state,
    widget_registry,
):
    print("Running thread...")
    try:
        t_type = str(task.get("type"))

        # HANDLE JQL SEARCH
        if t_type == "jql_search":
            print(f"task.get('type')={t_type}")
            config_data = task.get("config_data")
            payload = task.get("payload")
            headers = task.get("headers")
            proxies = task.get("proxies")
            thread_count = int(task.get("thread_count", 2))
            # ...existing JQL logic here...
            # After processing, switch panel
            print("Batch insert completed.")
            print(f"DEBUG: card_retainer before switch_panel: {card_retainer}")
            print(
                f"DEBUG: card_retainer types: {[type(x.get('key', '')) for x in card_retainer]}"
            )

            try:
                added_issues = []
                existing_issues = []
                issues = fetch_all_issues_threaded(
                    config_data, payload, headers, proxies, thread_count
                )
                print(f"len(issues)={len(issues)}")

                # Remove duplicates using card_retainer
                new_issues = []
                for issue in issues:
                    key_val_raw = issue.get("key", "")
                    print(f"DEBUG: key_val_raw={key_val_raw}, type={type(key_val_raw)}")
                    key_val = str(key_val_raw)
                    check = {"key": key_val}
                    print(
                        f"DEBUG: check={check}, card_retainer_types={[type(x.get('key', '')) for x in card_retainer]}"
                    )
                    if check in card_retainer:
                        existing_issues.append(key_val)
                        print("HERE!!! " + str(key_val))
                    else:
                        added_issues.append(key_val)
                        card_retainer.append({"key": key_val})
                        new_issues.append(issue)
                        # Ensure ticket is inserted into the database
                        from jira_manager.sql_manager import add_or_find_key_return_id
                        add_or_find_key_return_id(db_path, key_val)


                # Create the receipt in the database
                import os
                from jira_manager.sql_manager import insert_receipt
                db_path = os.path.join(os.path.dirname(__file__), "tickets.db")
                insert_receipt(db_path, existing_issues, added_issues)
                parent = widget_registry.get("jql_query").winfo_toplevel()

                # Show a simple popup to inform the user
                def show_receipt_popup():
                    master = widget_registry.get("jql_query").winfo_toplevel()
                    popup = tk.Toplevel(master)
                    popup.overrideredirect(True)  # Remove title bar
                    popup.resizable(False, False)
                    popup.transient(master)
                    popup.grab_set()
                    theme_manager.register(popup, "frame")
                    frame = tk.Frame(popup, padx=20, pady=20)
                    theme_manager.register(frame, "frame")
                    frame.pack(fill="both", expand=True, padx=1, pady=1)

                    def center_popup():
                        frame.update_idletasks()
                        w = frame.winfo_reqwidth() + 40
                        h = frame.winfo_reqheight() + 40
                        master.update_idletasks()
                        main_x = master.winfo_x()
                        main_y = master.winfo_y()
                        main_w = master.winfo_width()
                        main_h = master.winfo_height()
                        x = main_x + (main_w // 2) - (w // 2)
                        y = main_y + (main_h // 2) - (h // 2)
                        popup.geometry(f"{w}x{h}+{x}+{y}")
                        popup.lift()
                        popup.update_idletasks()
                        try:
                            popup.focus_force()
                            popup.focus_set()
                        except Exception:
                            pass

                    label = tk.Label(frame, text="A work receipt has been created.", font=("Trebuchet MS", 14, "bold"))
                    theme_manager.register(label, "label")
                    label.pack(pady=20)
                    def close_popup():
                        master.unbind("<Configure>")
                        popup.destroy()

                    close_btn = tk.Button(frame, text="Close", command=close_popup, font=("Segoe UI", 11, "bold"), cursor="hand2")
                    theme_manager.register(close_btn, "base_button")
                    close_btn.pack(pady=10)

                    center_popup()
                    master.bind("<Configure>", lambda e: center_popup())
                show_receipt_popup()

                # Add a button to the ticket panel to view receipts
                ticket_panel = parent.panel_choice.get("ticket_panel") if hasattr(parent, "panel_choice") else None
                if ticket_panel and not hasattr(ticket_panel, "_receipts_btn_added"):
                    def show_receipts_panel():
                        for child in parent.winfo_children():
                            child.pack_forget()
                        from jira_manager.custom_widgets import WorkReceiptsPanel
                        receipts_panel = WorkReceiptsPanel(parent, theme_manager=theme_manager)
                        receipts_panel.pack(fill="both", expand=True)
                    receipts_btn = tk.Button(ticket_panel, text="View Receipts", command=show_receipts_panel, font=("Trebuchet MS", 11, "bold"))
                    receipts_btn.pack(side="top", pady=8)
                    ticket_panel._receipts_btn_added = True

                # Always redirect to ticket_panel after showing receipt popup
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
                # If no new tickets, do NOT reload ticket panel
            except requests.exceptions.ConnectionError:
                print("You appear to be offline or unable to connect to the server.")
                run_error(
                    panel_choice,
                    ui_state,
                    widget_registry,
                    "You appear to be offline or unable to connect to the server.",
                )
            except requests.exceptions.HTTPError as err:
                print(err)
                run_error(
                    panel_choice,
                    ui_state,
                    widget_registry,
                    f"There was an issue with the request to Jira.\nReason = {err}",
                )
    except Exception as e:
        print(f"Error in JQL search handler: {e}")
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
        run_error(
            panel_choice,
            ui_state,
            widget_registry,
            "Missing Jira server, please provide information in the configuration panel.",
        )
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
            run_error(
                panel_choice,
                ui_state,
                widget_registry,
                "Missing Username or Password, please provide information in the configuration panel.",
            )
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
                run_error(
                    panel_choice,
                    ui_state,
                    widget_registry,
                    f"Failed to build headers using provided username/password.\nReason = {e}",
                )
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
            run_error(
                panel_choice,
                ui_state,
                widget_registry,
                "Missing Bearer Token, please provide information in the configuration panel.",
            )
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
                run_error(
                    panel_choice,
                    ui_state,
                    widget_registry,
                    f"Failed to build headers using provided Bearer Token.\nReason = {e}",
                )
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
    jql_task_queue,
    jql_worker_running,
    card_retainer,
    selected_items,
    root=None,
):
    db_path = "jira_manager/tickets.db"
    config_data = load_data()
    headers, proxies = configure_project_credentials(
        config_data, panel_choice, ui_state, widget_registry, root, theme_manager
    )
    jql_query = widget_registry.get("jql_query")

    # Use a mutable worker_state dictionary to track worker status
    if not hasattr(toolbar_action, "worker_state"):
        toolbar_action.worker_state = {"running": False}
    worker_state = toolbar_action.worker_state

    # Ensure jql_task_queue is a Queue object
    if not isinstance(jql_task_queue, Queue):
        jql_task_queue = Queue()

    # Ensure card_retainer is a list of dicts with 'key' as str
    if not isinstance(card_retainer, list):
        print(
            f"WARNING: card_retainer was type {type(card_retainer)}, resetting to empty list."
        )
        card_retainer = []
    else:
        # If card_retainer contains non-dict items, filter out
        card_retainer = [
            x
            for x in card_retainer
            if isinstance(x, dict) and isinstance(x.get("key", ""), str)
        ]

    # LOGIC FOR JIRA SEARCH PANEL
    if payload["type"] == "search_jiras":
        panel_choice["ticket_panel"].widget_registry.get("canvas").yview_moveto(0)
        # HANDLE FOR EMPTY SEARCH BAR
        if payload["jql"] == "Enter proper JQL query":
            run_error(panel_choice, ui_state, widget_registry, "Missing JQL Statement.")
            return
        try:
            print("Queueing JQL search task...")
            task = {
                "type": "jql_search",
                "config_data": config_data,
                "payload": payload,
                "headers": headers,
                "proxies": proxies,
                "thread_count": 4,  # Default to 4 threads for ticket fetching
            }
            jql_task_queue.put(task)
            # Clear the JQL entry after search
            if jql_query:
                jql_query.delete(0, "end")
            # Start worker if not running
            if not worker_state["running"]:
                worker_thread = Thread(
                    target=jql_worker,
                    args=(
                        panel_choice,
                        theme_manager,
                        card_retainer,
                        db_path,
                        selected_items,
                        ui_state,
                        widget_registry,
                        stop_flag,
                        jql_task_queue,
                        worker_state,
                    ),
                    daemon=True,
                )
                worker_thread.start()
        except requests.exceptions.ConnectionError:
            print("You appear to be offline or unable to connect to the server.")
        except Exception as e:
            run_error(
                theme_manager=theme_manager,
                root=root,
                message=f"There was an error queueing the JQL request.\nReason = {e}.",
            )
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
            card_retainer = (
                panel_choice.get("card_retainer")
                if panel_choice and hasattr(panel_choice, "get")
                else None
            )
            selected_items = (
                panel_choice.get("selected_items")
                if panel_choice and hasattr(panel_choice, "get")
                else None
            )
            switch_panel(
                "error_panel",
                ui_state,
                panel_choice,
                widget_registry,
                None,
                None,
                card_retainer,
                selected_items,
            )
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
