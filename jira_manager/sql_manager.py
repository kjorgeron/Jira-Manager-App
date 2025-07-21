import sqlite3


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
