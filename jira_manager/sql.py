tickets_table = """CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE
);
"""

fields_table = """CREATE TABLE fields (
    field_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    field_key TEXT NOT NULL,          -- e.g. "customfield_10011"
    field_name TEXT NOT NULL,         -- UI display name like "Assignee"
    field_type TEXT NOT NULL,         -- Jira schema type like "user", "string"
    widget_type TEXT NOT NULL,        -- UI widget used, e.g. "Dropdown"
    is_editable INTEGER DEFAULT 1,    -- Flag from 'operations'
    allowed_values TEXT,              -- JSON string of allowed options (if any)
    current_value TEXT,               -- Raw current field value (to prefill)
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);
"""
