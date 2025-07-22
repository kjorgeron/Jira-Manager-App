import sqlite3

def insert_fields_into_db(db_path, ticket_id, field_rows):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for field in field_rows:
                cursor.execute("""
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
                """, (
                    ticket_id,
                    field["field_key"],
                    field["field_name"],
                    field["field_type"],
                    field["widget_type"],
                    field["is_editable"],
                    field["allowed_values"],
                    field["current_value"]
                ))
            conn.commit()
    except Exception as e:
        print(f"[SQL Error] {e}")


def run_sql_stmt(db_path, sql: str = None, table_name: str = None, data: dict = None, stmt_type: str = None):
    items = None

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            stmt_type = stmt_type.lower() if stmt_type else ""

            if stmt_type == "select":
                if sql:
                    cursor.execute(sql)
                    items = cursor.fetchall()
                else:
                    raise ValueError("SELECT operation requires an SQL query.")

            elif stmt_type == "insert":
                if table_name and data:
                    columns = ", ".join(data.keys())
                    placeholders = ", ".join(["?" for _ in data])
                    values = tuple(data.values())
                    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    cursor.execute(sql, values)
                    conn.commit()
                else:
                    raise ValueError("INSERT operation requires table_name and data.")

            elif stmt_type in {"update", "delete", "create", "drop", "alter"}:
                if sql:
                    cursor.execute(sql)
                    conn.commit()
                else:
                    raise ValueError(f"{stmt_type.upper()} operation requires an SQL query.")

            else:
                raise ValueError(f"Unsupported statement type: {stmt_type}")

            cursor.close()

    except Exception as e:
        print(f"[SQL Error] {e}")

    return items


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


def create_table(db_name: str, table_name: str, columns: dict):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    column_defs = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"

    cursor.execute(sql)
    conn.commit()
    conn.close()


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


def read_from_table(db_name: str, table_name: str, filters: dict = None):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    if filters:
        conditions = " AND ".join([f"{col}=?" for col in filters])
        sql = f"SELECT * FROM {table_name} WHERE {conditions}"
        values = tuple(filters.values())
    else:
        sql = f"SELECT * FROM {table_name}"
        values = ()

    cursor.execute(sql, values)
    rows = cursor.fetchall()
    conn.close()
    return rows


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

    items = run_sql_stmt(db_path, select, stmt_type="select")
    if items != None:
        if len(items) > 0:
            print(f"Item {key} found in database.\nRecords = {items}")
            ticket_id, key = items[0]
            return ticket_id
        else:
            # ADD MISSING KEY TO DATABASE
            payload = {"key": key}
            run_sql_stmt(db_path, table_name="tickets", data=payload, stmt_type="insert")
            items = run_sql_stmt(db_path, select, stmt_type="select")
            if len(items) > 0:
                print(f"Item created successfully!\nRecords = {items}")
                ticket_id, key = items[0]
                return ticket_id
            else:
                print(f"Issue adding {key} to database")
                return 0
