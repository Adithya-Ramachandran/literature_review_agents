import streamlit as st
import pandas as pd
from src.streamlit_utils import get_all_papers, safe_json_loads, format_metrics, format_simple_list

st.set_page_config(layout="wide", page_title="Comparison Table")

st.title("📊 Comparative Analysis of Papers")
st.markdown("View key experimental details across all processed papers.")

# Load all paper data
# check to ensure the session state is initialized.
if 'db_path' not in st.session_state:
    st.warning("Please navigate to the main 'Paper Explorer' page first to connect to the database.")
    st.stop() # Stop the page from rendering further

df = get_all_papers(st.session_state.db_path)

if df.empty:
    st.warning(f"The database at `{st.session_state.db_path}` is empty. Process papers using `main.py` to see the comparison.")
else:
    # --- Prepare the data for display ---

    # 1. Create a unique, readable ID from the file path
    # e.g., "data/papers/3.pdf" -> "3"
    try:
        df['ID'] = df['path'].str.split(r'[\\/]').str[-1].str.replace('.pdf', '', regex=False)
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce')

        df = df.sort_values('ID', ascending=True)
        print(df['ID'])
        print(df['ID'].dtypes)

    except Exception:
        df['ID'] = df['path']  # Fallback

    # 2. Select the columns you want to compare
    columns_to_show = [
        'ID',
        'title',
        'year',

        'proposed_model_name',
        'experimental_methods',

        "dataset_name",
        "data_description",

        "source_type",
        "dataset_duration",
        "granularity_scale",
        "resolution",

        "data_preprocessing",
        "features_used",
        "train_test_split",

        "horizon",
        "metrics",

        "data_availability",
        "code_availability"
    ]

    # Ensure all required columns exist in the DataFrame, adding empty ones if not
    for col in columns_to_show:
        if col not in df.columns:
            df[col] = ""

    # Create a working copy for our transformations
    comparison_df = df.copy()

    # --- 2. Create the unique ID ---
    try:
        comparison_df['ID'] = comparison_df['path'].str.split(r'[\\/]').str[-1].str.replace('.pdf', '', regex=False)
    except Exception:
        comparison_df['ID'] = comparison_df['path']

    # --- 3. Apply the correct formatting to each list-based column ---
    # Use our new generic formatter for simple lists
    comparison_df['experimental_methods'] = comparison_df['experimental_methods'].apply(format_simple_list)
    comparison_df['data_preprocessing'] = comparison_df['data_preprocessing'].apply(format_simple_list)
    comparison_df['features_used'] = comparison_df['features_used'].apply(format_simple_list)

    # Use our special, more complex formatter for the metrics column
    comparison_df['metrics'] = comparison_df['metrics'].apply(format_metrics)

    # --- 4. Select and rename columns for a professional display ---
    # First, select only the columns we want in the desired order
    comparison_df = comparison_df[columns_to_show]

    # Second, rename them to be human-readable
    comparison_df.rename(columns={
        'title': 'Title',
        'year': 'Year',
        'proposed_model_name': 'Proposed Model',
        'experimental_methods': 'Methods Evaluated',
        'dataset_name': 'Dataset Name',
        'data_description': 'Data Description',
        'source_type': 'Source Type',
        'dataset_duration': 'Dataset Duration',
        'granularity_scale': 'Granularity / Scale',
        'resolution': 'Resolution',
        'data_preprocessing': 'Preprocessing Steps',
        'features_used': 'Features Used',
        'train_test_split': 'Train/Test Split',
        'horizon': 'Horizon',
        'metrics': 'Metrics',
        'data_availability': 'Data Availability',
        'code_availability': 'Code Availability'
    }, inplace=True)

    # --- 5. Display the final, interactive table ---
    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )