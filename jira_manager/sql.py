tickets_table = """CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    needs_update INTEGER DEFAULT 0
);
"""

fields_table = """CREATE TABLE IF NOT EXISTS fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER,
    field_key TEXT,
    field_name TEXT,
    field_type TEXT,
    widget_type TEXT,
    is_editable TEXT,
    allowed_values TEXT,
    current_value TEXT,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);
"""
