import streamlit as st
import pandas as pd
from src.streamlit_utils import get_all_papers, safe_json_loads
import sys


# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Paper Explorer")

st.title("📖 LLM based Literature Survey: Paper Explorer")
st.markdown("---")

if 'db_path' not in st.session_state:
    # 2. If not, this is the first run. Determine the path.
    DEFAULT_DB_PATH = "db/paper.db"

    # sys.argv is a list of command-line arguments.
    # sys.argv[0] is the script name ('app.py').
    # sys.argv[1] is the first argument after the script name.
    if len(sys.argv) > 1:
        # A path was provided from the command line
        st.session_state.db_path = sys.argv[1]
    else:
        # No path was provided, use the default
        st.session_state.db_path = DEFAULT_DB_PATH

st.sidebar.info(f"Connected to: `{st.session_state.db_path}`")


# --- Main Display Area ---
df = get_all_papers(st.session_state.db_path)

if df.empty:
    st.warning("The database is empty. Please process papers using `main.py` first.")
else:
    # Sidebar for paper selection
    df['id_str'] = df['path'].str.split(r'[\\/]').str[-1].str.replace('.pdf', '', regex=False)
    df['ID'] = pd.to_numeric(df['id_str'], errors='coerce')
    df.dropna(subset=['ID'], inplace=True)
    df['ID'] = df['ID'].astype(int)
    df.sort_values(by='ID', inplace=True)
    df['display_title'] = df['ID'].astype(str) + " : " + df['title'].fillna('Untitled')

    # --- Sidebar for paper selection ---
    st.sidebar.title("📄 Select Paper")

    # Sidebar for paper selection now uses the new display format
    selected_title = st.sidebar.radio(
        "Choose a paper to view its details:",
        df['display_title'],
        label_visibility="collapsed"
    )

    paper_data = df[df['display_title'] == selected_title].iloc[0]

    # --- Display Paper Details (This part is unchanged) ---
    st.header(paper_data['title'])

    authors_list = safe_json_loads(paper_data['authors'])
    st.subheader(f"By *{', '.join(authors_list)}*")

    doi_value = paper_data.get('doi', '')

    doi_display_string = ""
    if doi_value:
        if doi_value.startswith('http'):
            full_doi_url = doi_value
        else:
            full_doi_url = f"https://doi.org/{doi_value}"
        doi_display_string = f"**DOI:** [{doi_value}]({full_doi_url})"
    else:
        # Fallback if no DOI was extracted for this paper.
        doi_display_string = "**DOI:** Not Available"

    st.caption(
        f"**Journal:** {paper_data.get('journal', 'N/A')} | **Year:** {paper_data.get('year', 'N/A')} | {doi_display_string}")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Abstract")
        st.write(paper_data['abstract'])
        st.subheader("Problem Statement")
        st.info(paper_data['problem_statement'])
        st.subheader("Methodology")
        st.success(paper_data['methodology'])

    with col2:
        st.subheader("Main Findings")
        st.success(paper_data['main_findings'])
        st.subheader("Unique Contribution (USP)")
        st.info(paper_data['usp'])
        st.subheader("Limitations")
        st.warning(paper_data['limitations'])

    st.markdown("---")
    st.header("Data & Experimental Details")

    col3, col4, col5 = st.columns(3)
    with col3:
        st.subheader("Prediction Horizon")
        st.write(paper_data['horizon'])
    with col4:
        st.subheader("Data Resolution")
        st.write(paper_data['resolution'])
    with col5:
        st.subheader("Data Availability")
        st.write(paper_data['data_availability'])

    st.subheader("Data Description")
    st.write(paper_data['data_description'])
    st.subheader("Metrics & Performance")
    metrics_list = safe_json_loads(paper_data['metrics'])
    st.write(', '.join(metrics_list))