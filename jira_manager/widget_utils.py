from jira_manager.file_manager import load_data


def map_fields_to_widgets(editable_fields, current_issue_fields=None, parent=None):
    import tkinter as tk
    from jira_manager.custom_widgets import EntryWithPlaceholder
    # Map DB widget_type to Tkinter widget class
    widget_map = {
        "entry": EntryWithPlaceholder,
        "combobox": tk.ttk.Combobox if hasattr(tk, 'ttk') else None,
        "label": tk.Label,
        # Add more mappings as needed
    }

    config = load_data()
    HIDDEN_FIELDS = config.get("hidden_fields", [])

    widgets = []
    for fid, fdata in editable_fields.items():
        field_name = fdata.get("name", fid)
        if field_name in HIDDEN_FIELDS:
            continue
        value = fdata.get("value", "")
        options = fdata.get("options", [])
        # If options are not provided, default to empty list
        if options is None:
            options = []

        # Add a divider between fields for visual separation
        divider = tk.Frame(parent, height=2, bg="#222", bd=0)
        divider.pack(fill="x", padx=12, pady=(12, 0))
        divider._theme_role = "divider"
        widgets.append(divider)

        # Pack a label for the field name (bold, larger, left-aligned)
        label_widget = tk.Label(parent, text=field_name, font=("Trebuchet MS", 13, "bold"), anchor="w")
        label_widget.pack(fill="x", padx=18, pady=(6,2))
        label_widget._theme_role = "label"
        widgets.append(label_widget)

        # Decide widget type: Combobox for few options, Entry for many
        if len(options) > 0 and len(options) <= 20:
            input_widget = tk.ttk.Combobox(parent, values=options, font=("Trebuchet MS", 12), justify="left")
            if value:
                input_widget.set(value)
            input_widget._theme_role = "combobox"
            input_widget.pack(fill="x", padx=18, pady=(0,10))
        else:
            input_widget = EntryWithPlaceholder(parent, placeholder=field_name, initial_text=value)
            input_widget._theme_role = "placeholder_entry"
            input_widget.pack(fill="x", padx=18, pady=(0,10))
        widgets.append(input_widget)

    return widgets