import sqlite3
import json
from src.initialise_state import State
from definitions import DB_PATH, TABLE_NAME


def create_database():
    """
    Creates the SQLite database and the 'papers' table if they don't exist.
    The table schema is derived from the State TypedDict, with specific types.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Define schema with specific types ---
    fields = []

    # Generate the CREATE TABLE SQL command dynamically from the State keys
    # This makes it easy to update if you add more fields to your State
    fields_ = [k for k in State.__annotations__.keys() if
                   k not in ['messages', 'raw_text', 'landmarks', 'ocr_needed']]

    for key in fields_:
        if key == 'path':
            fields.append(f"    {key} TEXT PRIMARY KEY")
        elif key == 'year':
            fields.append(f"    {key} INTEGER")  # <-- Specific type for year
        else:
            fields.append(f"    {key} TEXT")


    # Use path as the primary key as it's unique for each file
    fields_with_newlines = ",\n".join(fields)

    create_table_sql = f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                            {fields_with_newlines}
                            );
                            """

    cursor.execute(create_table_sql)
    conn.commit()
    conn.close()
    print("Database and table are ready.")


def reinitialize_database():
    """
    Completely wipes and reinitializes the database.
    This function will drop the 'papers' table if it exists, deleting all data,
    and then create a new, empty table.
    """
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"--- Reinitializing Database: Dropping table '{TABLE_NAME}'... ---")

    # SQL command to drop the table. "IF EXISTS" prevents errors if the table isn't there.
    drop_table_sql = f"DROP TABLE IF EXISTS {TABLE_NAME}"

    # Execute the command
    cursor.execute(drop_table_sql)

    # Commit the change (the table is now gone)
    conn.commit()
    conn.close()

    print(f"--- Table '{TABLE_NAME}' successfully dropped. ---")

    # Now, call the existing create_database function to build a fresh table
    # This is a great example of code reuse.
    print(f"--- Creating a new, empty '{TABLE_NAME}' table... ---")
    create_database()


def prepare_data_for_db(data: State) -> dict:
    """
    Cleans the final state, converts data types, and removes fields
    that are not meant for database storage.
    """
    # Start with a copy of the data to avoid modifying the original state object
    prepared_data = data.copy()

    # --- 1. Remove Internal Fields ---
    # These fields are for graph logic only and should not be stored.
    fields_to_remove = ['messages', 'raw_text', 'landmarks', 'ocr_needed']
    for field in fields_to_remove:
        prepared_data.pop(field, None)

    # --- 2. Perform Type Conversions ---
    # Convert 'year' to integer, with a fallback for non-numeric values
    year_str = prepared_data.get('year')
    if year_str and isinstance(year_str, str) and year_str.isdigit():
        prepared_data['year'] = int(year_str)
    elif not isinstance(year_str, int):
        prepared_data['year'] = None  # Set to None if it's not a valid number

    # --- 3. Serialize Complex Types to JSON Strings ---
    # This loop handles all fields that are lists or dictionaries.
    for key, value in prepared_data.items():
        if isinstance(value, (list, dict)):
            prepared_data[key] = json.dumps(value)
        elif isinstance(value, bool):
            # Convert booleans to a string representation for the TEXT column
            prepared_data[key] = str(value)

    # --- 4. Handle Nulls and Ensure Consistency ---
    # Ensure all remaining values are of a type that can be inserted (str, int, float, None)
    for key, value in prepared_data.items():
        if value is None:
            prepared_data[key] = ""  # Use empty string for None to be safe with TEXT columns, except for year

    # Special handling for year to allow NULL
    if prepared_data.get('year') == "":
        prepared_data['year'] = None

    return prepared_data


def upsert_paper(data: State):
    """
    Inserts a new paper record or replaces an existing one.
    It now uses the prepare_data_for_db function first.
    """
    # --- THIS IS THE KEY CHANGE ---
    data_to_insert = prepare_data_for_db(data)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    columns = ', '.join(data_to_insert.keys())
    placeholders = ', '.join(['?'] * len(data_to_insert))

    sql = f"INSERT OR REPLACE INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"

    try:
        cursor.execute(sql, list(data_to_insert.values()))
        conn.commit()
        print(f"--- SUCCESS: Saved data for: {data['path']} to database. ---")
    except sqlite3.Error as e:
        print(f"--- DATABASE ERROR: Failed to upsert data for {data['path']}. Error: {e} ---")
    finally:
        conn.close()


def paper_exists(path: str) -> bool:
    """
    Checks if a paper with the given path already exists in the database.

    Args:
        path (str): The file path of the paper, which is the primary key.

    Returns:
        bool: True if the paper exists, False otherwise.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # A more efficient query than SELECT *; we just need to know if a row exists.
    # The `LIMIT 1` ensures the database stops searching as soon as it finds a match.
    query = f"SELECT 1 FROM {TABLE_NAME} WHERE path = ? LIMIT 1"

    cursor.execute(query, (path,))
    result = cursor.fetchone()

    conn.close()

    # fetchone() returns a tuple (e.g., (1,)) if a record is found, otherwise None.
    # So, checking if the result is not None gives us our boolean.
    return result is not None
