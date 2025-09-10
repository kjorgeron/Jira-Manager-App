def create_receipts_table(db_path):
    from jira_manager.sql import receipts_table
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(receipts_table)
        conn.commit()

def insert_receipt(db_path, existing_tickets, added_tickets):
    import datetime, json
    create_receipts_table(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO receipts (created_at, existing_tickets, added_tickets) VALUES (?, ?, ?)",
            (
                datetime.datetime.now().isoformat(),
                json.dumps(existing_tickets),
                json.dumps(added_tickets)
            )
        )
        conn.commit()

def fetch_all_receipts(db_path):
    create_receipts_table(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT receipt_id, created_at, existing_tickets, added_tickets FROM receipts ORDER BY created_at DESC")
        rows = cursor.fetchall()
    import json
    return [
        {
            "receipt_id": row[0],
            "created_at": row[1],
            "existing_tickets": json.loads(row[2]),
            "added_tickets": json.loads(row[3])
        }
        for row in rows
    ]
import sqlite3

# def insert_fields_into_db(db_path, ticket_id, field_rows):
#     try:
#         with sqlite3.connect(db_path) as conn:
#             cursor = conn.cursor()
#             for field in field_rows:
#                 cursor.execute("""
#                     INSERT INTO fields (
#                         ticket_id,
#                         field_key,
#                         field_name,
#                         field_type,
#                         widget_type,
#                         is_editable,
#                         allowed_values,
#                         current_value
#                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#                 """, (
#                     ticket_id,
#                     field["field_key"],
#                     field["field_name"],
#                     field["field_type"],
#                     field["widget_type"],
#                     field["is_editable"],
#                     field["allowed_values"],
#                     field["current_value"]
#                 ))
#             conn.commit()
#     except Exception as e:
#         print(f"[SQL Error] {e}")


# def run_sql_stmt(db_path, sql: str = None, table_name: str = None, data: dict = None, stmt_type: str = None, params: tuple = None):

#     print(f"Running sql type {stmt_type}")
#     items = None
#     try:
#         with sqlite3.connect(db_path) as conn:
#             cursor = conn.cursor()

#             stmt_type = stmt_type.lower() if stmt_type else ""

#             if stmt_type == "select":
#                 if sql:
#                     if params:
#                         cursor.execute(sql, params)
#                         items = cursor.fetchall()
#                     else:
#                         cursor.execute(sql)
#                         items = cursor.fetchall()
#                 else:
#                     raise ValueError("SELECT operation requires an SQL query.")

#             elif stmt_type == "insert":
#                 cursor.execute(sql, params)
#                 conn.commit()
#                 conn.close()

#             elif stmt_type in {"update", "delete", "create", "drop", "alter"}:
#                 if sql:
#                     if not params:
#                         cursor.execute(sql)
#                         conn.commit()
#                     else:
#                         cursor.execute(sql, params)
#                         conn.commit()
#                 else:
#                     raise ValueError(f"{stmt_type.upper()} operation requires an SQL query.")

#             else:
#                 raise ValueError(f"Unsupported statement type: {stmt_type}")

#             cursor.close()

#     except Exception as e:
#         print(f"[SQL Error] {e}")

#     return items


def run_sql_stmt(
    db_path,
    sql: str = None,
    table_name: str = None,
    data: dict = None,
    stmt_type: str = None,
    params: tuple = None,
):
    print(f"Running sql type {stmt_type}")
    items = None

    stmt_type = stmt_type.lower() if stmt_type else ""

    try:
        # Create a new connection for each call
        conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")  # Enable WAL mode
        conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints
        cursor = conn.cursor()

        if stmt_type == "select":
            if not sql:
                raise ValueError("SELECT operation requires an SQL query.")
            cursor.execute(sql, params or ())
            items = cursor.fetchall()

        elif stmt_type == "insert":
            if not sql:
                raise ValueError("INSERT operation requires an SQL query.")
            cursor.execute(sql, params or ())
            conn.commit()

        elif stmt_type in {"update", "delete", "create", "drop", "alter"}:
            if not sql:
                raise ValueError(
                    f"{stmt_type.upper()} operation requires an SQL query."
                )
            cursor.execute(sql, params or ())
            conn.commit()

        else:
            raise ValueError(f"Unsupported statement type: {stmt_type}")

        cursor.close()
        conn.close()

    except sqlite3.OperationalError as e:
        print(f"[SQL Error] {e}")

    return items


def batch_insert_tickets(db_path, tickets):
    try:
        conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        keys = [(ticket["key"],) for ticket in tickets]
        cursor.executemany("INSERT INTO tickets (key) VALUES (?)", keys)

        conn.commit()
        cursor.close()
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"[SQL Error] {e}")


def table_exists(db_path, table_name):
    """
    Checks if a table exists in the SQLite database.

    Args:
        db_path (str): Path to the SQLite database file.
        table_name (str): Name of the table to check.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """,
            (table_name,),
        )
        result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    finally:
        conn.close()


# def create_table(db_name: str, table_name: str, columns: dict):
#     conn = sqlite3.connect(db_name)
#     cursor = conn.cursor()

#     column_defs = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
#     sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"

#     cursor.execute(sql)
#     conn.commit()
#     conn.close()


def insert_into_table(db_name: str, table_name: str, data: dict):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    values = tuple(data.values())

    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    cursor.execute(sql, values)
    conn.commit()
    conn.close()


# def read_from_table(db_name: str, table_name: str, filters: dict = None):
#     conn = sqlite3.connect(db_name)
#     cursor = conn.cursor()

#     if filters:
#         conditions = " AND ".join([f"{col}=?" for col in filters])
#         sql = f"SELECT * FROM {table_name} WHERE {conditions}"
#         values = tuple(filters.values())
#     else:
#         sql = f"SELECT * FROM {table_name}"
#         values = ()

#     cursor.execute(sql, values)
#     rows = cursor.fetchall()
#     conn.close()
#     return rows


def add_column_to_table(
    db_path, table_name, column_name, column_type="TEXT", default_value=None
):
    """
    Adds a new column to an existing SQLite table.

    Args:
        db_path (str): Path to the SQLite database file.
        table_name (str): Name of the table to modify.
        column_name (str): Name of the new column.
        column_type (str): SQLite data type (e.g., TEXT, INTEGER, REAL).
        default_value (any): Optional default value for the column.

    Returns:
        bool: True if successful, False if column already exists or error occurs.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [col[1] for col in cursor.fetchall()]
        if column_name in existing_columns:
            print(f"Column '{column_name}' already exists in '{table_name}'.")
            return False

        # Build ALTER TABLE statement
        alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value is not None:
            alter_stmt += f" DEFAULT {repr(default_value)}"

        cursor.execute(alter_stmt)
        conn.commit()
        print(f"Column '{column_name}' added to '{table_name}'.")
        return True

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False

    finally:
        conn.close()


def add_or_find_key_return_id(db_path: str, key: str) -> int:

    select = f"""
        SELECT * FROM tickets WHERE key = '{key}';
    """
    print(f"{key=}")
    items = run_sql_stmt(db_path, select, stmt_type="select")
    print(f"{items=}")
    if items != None:
        if len(items) > 0:
            print(f"Item {key} found in database.\nRecords = {items}")
            ticket_id, key, needs_update = items[0]
            return ticket_id
        else:
            # ADD MISSING KEY TO DATABASE
            run_sql_stmt(
                db_path,
                sql="INSERT INTO tickets (key) VALUES (?)",
                stmt_type="insert",
                params=(key,)
            )
            items = run_sql_stmt(db_path, select, stmt_type="select")
            if items and len(items) > 0:
                print(f"Item created successfully!\nRecords = {items}")
                ticket_id, key, needs_update = items[0]
                return ticket_id
            else:
                print(f"Issue adding {key} to database")
                return 0


def add_or_find_field_return_id(db_path: str, ticket_id: int, field: dict) -> int:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if field exists for given ticket_id and field_key
            cursor.execute(
                """
                SELECT id FROM fields
                WHERE ticket_id = ? AND field_key = ?;
            """,
                (ticket_id, field["field_key"]),
            )

            result = cursor.fetchone()
            if result:
                print(
                    f"Field {field['field_key']} already exists.\nRecord ID = {result[0]}"
                )
                return result[0]

            # Insert new field
            cursor.execute(
                """
                INSERT INTO fields (
                    ticket_id,
                    field_key,
                    field_name,
                    field_type,
                    widget_type,
                    is_editable,
                    allowed_values,
                    current_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    ticket_id,
                    field["field_key"],
                    field["field_name"],
                    field["field_type"],
                    field["widget_type"],
                    field["is_editable"],
                    field["allowed_values"],
                    field["current_value"],
                ),
            )

            conn.commit()
            return cursor.lastrowid

    except Exception as e:
        print(f"[SQL Error] {e}")
        return 0
