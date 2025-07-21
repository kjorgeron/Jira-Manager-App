import sqlite3


def run_sql_stmt(db_path, sql):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)

        requires_commit = [
            # Data manipulation
            "INSERT",  # Add new rows
            "UPDATE",  # Modify existing rows
            "DELETE",  # Remove rows
            # Table/schema changes
            "CREATE TABLE",  # Create new table
            "DROP TABLE",  # Delete table
            "ALTER TABLE",  # Modify table structure
            # Index and view management (less common but relevant)
            "CREATE INDEX",
            "DROP INDEX",
            "CREATE VIEW",
            "DROP VIEW",
            # Trigger and transaction control
            "CREATE TRIGGER",
            "DROP TRIGGER",
            "BEGIN TRANSACTION",  # When manually controlling transactions
            "END TRANSACTION",  # Required if using BEGIN manually
        ]
        for require in requires_commit:
            if require in sql:
                conn.commit()
        cursor.close()
    except:
        pass


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
