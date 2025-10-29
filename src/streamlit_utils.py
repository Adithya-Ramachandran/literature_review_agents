import streamlit as st
import sqlite3
import pandas as pd
import json
import os


# We cache the data loading to make the app faster.
@st.cache_data
def get_all_papers(db_path: str):
    """Fetches all paper data from a dynamically provided database path."""
    if not os.path.exists(db_path):
        st.error(f"Database file not found at: {db_path}")
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM papers", conn)
        conn.close()
        return df
    except pd.errors.DatabaseError:
        # This can happen if the DB file is empty or the table doesn't exist.
        return pd.DataFrame()


def safe_json_loads(s):
    """Safely loads a JSON string, returning an empty list if it fails."""
    if not s or pd.isna(s):
        return []
    try:
        # Handle cases where the string might be a representation of a list of strings
        s = s.replace("'", "\"")
        data = json.loads(s)
        # Ensure the output is a list for consistency
        return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, TypeError):
        # If it's just a plain string, return it in a list
        return [s] if s else []


def format_metrics(metrics_json_string: str) -> str:
    """
    Intelligently formats the 'metrics' data for display.
    This version is robust and handles lists containing a mix of strings and dictionaries.
    """
    data = safe_json_loads(metrics_json_string)

    if not data or not isinstance(data, list):
        return ""  # Return empty if there's no data or it's not a list

    # --- NEW ROBUST LOGIC ---
    # Create a new list to hold the properly formatted string for each item.
    formatted_parts = []

    # Iterate through each item in the list individually.
    for item in data:
        if isinstance(item, str):
            # If it's a string, add it directly.
            formatted_parts.append(item)
        elif isinstance(item, dict):
            # If it's a dictionary, format it into "name: value".
            if 'name' in item and 'value' in item:
                formatted_parts.append(f"{item['name']}: {item['value']}")
            else:
                # Fallback for unexpected dictionary structures.
                formatted_parts.append(str(item))
        else:
            # Fallback for any other unexpected data type.
            formatted_parts.append(str(item))

    # Join the final list of formatted strings. Using a semicolon is good for readability.
    return "; ".join(formatted_parts)


def format_simple_list(json_string: str) -> str:
    """
    Formats a JSON string representing a simple list of items
    into a human-readable, comma-separated string.
    """
    data = safe_json_loads(json_string)

    if not data or not isinstance(data, list):
        return ""

    # Ensure all items are strings before joining
    return ", ".join(map(str, data))